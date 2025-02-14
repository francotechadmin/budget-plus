import io
import calendar
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.database import get_db
from ..models.models import Transaction, Category, Section
from ..schemas.schemas import UpdateTransactionRequest

# Import Elasticsearch helper classes
from ..elasticsearch_simple_client.uploader import Uploader
from ..elasticsearch_simple_client.searcher import Searcher

# Import authentication helper
from ..auth import get_current_user

router = APIRouter()

@router.post("/", summary="Upload bank transactions")
async def upload_bank_transactions(
    files: list[UploadFile] = File(...), 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload bank transactions via CSV files.
    The endpoint detects the source (e.g. Chase or Citi) based on column names
    and processes the file accordingly.
    """
    logging.info(f"Uploading {len(files)} file(s)...")
    
    # Expected columns for each bank format
    chase_debit_columns = [
        'Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance', 'Check or Slip #'
    ]
    chase_credit_columns = [
        'Transaction Date', 'Post Date', 'Description', 'Category', 'Type', 'Amount', 'Memo'
    ]
    citi_columns = ['Status', 'Date', 'Description', 'Debit', 'Credit']

    new_transactions = []
    searcher = Searcher()

    for file in files:
        # Determine file source by reading the header
        try:
            df_preview = pd.read_csv(file.file, nrows=1)
            if 'Posting Date' in df_preview.columns:
                source = 'chase_debit'
            elif 'Post Date' in df_preview.columns:
                source = 'chase_credit'
            elif 'Date' in df_preview.columns:
                source = 'citi'
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
        
        # Reset pointer for full read
        file.file.seek(0)
        
        try:
            if source == 'chase_debit':
                df = pd.read_csv(file.file, usecols=chase_debit_columns)
                df = df.rename(columns={
                    'Description': 'description',
                    'Posting Date': 'date',
                    'Amount': 'amount',
                })
            elif source == 'citi':
                df = pd.read_csv(file.file, usecols=citi_columns)
                # Calculate amount (debit negative, credit positive)
                df['amount'] = df['Debit'].fillna(0) * -1 + df['Credit'].fillna(0)
                df = df.rename(columns={
                    'Description': 'description',
                    'Date': 'date',
                })
                df = df[df['amount'].notna()]
            else:  # chase_credit
                df = pd.read_csv(file.file, usecols=chase_credit_columns)
                df = df.rename(columns={
                    'Description': 'description',
                    'Post Date': 'date',
                    'Amount': 'amount',
                })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
        
        for _, row in df.iterrows():
            # Check for duplicates by matching description, date, and amount for current user
            existing_txn = (
                db.query(Transaction)
                .filter(
                    Transaction.description == row['description'],
                    Transaction.date == row['date'],
                    Transaction.amount == row['amount'],
                    Transaction.user_id == current_user["sub"]
                )
                .first()
            )
            if existing_txn:
                continue

            # Use the searcher to determine the annotated category from the transaction description.
            es_result = searcher.execute_search(
                field="description",
                shoulds=[row['description']]
            )["hits"]["hits"]
            annotated_category = es_result[0]["_source"]["annotated_category"] if es_result else "Uncategorized"
            
            # Look up the Category in our database by name
            cat_entry = db.query(Category).filter(Category.name == annotated_category).first()
            if not cat_entry:
                # Optionally, you might want to create an "Uncategorized" category if it doesn't exist.
                cat_entry = db.query(Category).filter(Category.name == "Uncategorized").first()
                if not cat_entry:
                    raise HTTPException(status_code=400, detail="No valid category found for transaction.")
            
            # Create the transaction using the foreign key to Category
            new_txn = Transaction(
                user_id=current_user["sub"],
                description=row['description'],
                date=row['date'],
                amount=row['amount'],
                category_id=cat_entry.id
            )
            new_transactions.append(new_txn)
        
    if new_transactions:
        db.bulk_save_objects(new_transactions)
        db.commit()
        logging.info(f"Inserted {len(new_transactions)} new transactions.")
    else:
        logging.info("No new transactions to insert.")

    return get_transactions(db, current_user)


@router.get("/", summary="Get all transactions")
def get_transactions(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve all transactions for the current user.
    Joins the Transaction, Category, and Section tables to return human-readable names.
    """
    txns = (
        db.query(Transaction, Category.name.label("category_name"), Section.name.label("section_name"))
        .join(Category, Transaction.category_id == Category.id)
        .join(Section, Category.section_id == Section.id)
        .filter(Transaction.user_id == current_user["sub"])
        .all()
    )
    return [
        {
            "id": txn.id,
            "description": txn.description,
            "date": txn.date,
            "amount": txn.amount,
            "category": cat_name,
            "section": sec_name,
        }
        for txn, cat_name, sec_name in txns
    ]


@router.get("/{year}/{month}", summary="Get transactions for a specific month")
def get_transactions_by_month(year: int, month: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Retrieve transactions for a given month, grouped by section and category.
    """
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    txns = (
        db.query(Transaction)
        .join(Category)
        .join(Section)
        .filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.user_id == current_user["sub"]
        )
        .all()
    )

    grouped = {}
    for txn in txns:
        # Use relationships to access category and section names.
        section_name = txn.category.section.name if txn.category and txn.category.section else "Unknown"
        category_name = txn.category.name if txn.category else "Unknown"
        grouped.setdefault(section_name, {}).setdefault(category_name, []).append({
            "id": txn.id,
            "description": txn.description,
            "date": txn.date,
            "amount": txn.amount,
        })
    
    # Optionally, move the "Income" section to the top of the result.
    sorted_grouped = {}
    if "Income" in grouped:
        sorted_grouped["Income"] = grouped.pop("Income")
    for section, cats in sorted(grouped.items()):
        sorted_grouped[section] = cats
    return sorted_grouped


@router.get("/expenses/{year}/{month}", summary="Get expense totals for a month")
def get_transactions_expenses(year: int, month: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Calculate expense totals for a specific month.
    Filters out Income and Transfer transactions.
    """
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    txns = (
        db.query(Transaction)
        .join(Category)
        .join(Section)
        .filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.user_id == current_user["sub"],
            Section.name != 'Income',
            Category.name != 'Transfer'
        )
        .all()
    )

    totals = {}
    for txn in txns:
        category_name = txn.category.name if txn.category else "Unknown"
        totals.setdefault(category_name, 0)
        totals[category_name] += txn.amount
    return totals


@router.get("/totals/{year}/{month}", summary="Get income and expenses totals for a month")
def get_transactions_totals(year: int, month: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Returns the total income and total expenses for the specified month.
    """
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    txns = (
        db.query(Transaction)
        .join(Category)
        .join(Section)
        .filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.user_id == current_user["sub"]
        )
        .all()
    )

    income_total = sum(
        txn.amount 
        for txn in txns 
        if txn.category and txn.category.section and txn.category.section.name == 'Income'
    )
    expenses_total = sum(
        txn.amount 
        for txn in txns 
        if not (txn.category and txn.category.section and txn.category.section.name == 'Income')
    )
    return {"income": income_total, "expenses": expenses_total}


@router.get("/history", summary="Get transaction history for the last six months")
def get_transactions_history(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Returns a history of transactions aggregated by month for the last six months.
    """
    six_months_ago = pd.to_datetime("today") - pd.DateOffset(months=6)
    six_months_ago = six_months_ago.replace(day=1)
    
    txns = (
        db.query(Transaction)
        .join(Category)
        .join(Section)
        .filter(
            Transaction.date >= six_months_ago,
            Transaction.user_id == current_user["sub"],
            Category.name != 'Transfer'
        )
        .all()
    )

    history = {}
    for txn in txns:
        key = txn.date.strftime("%B %Y")
        if key not in history:
            history[key] = {"income": 0, "expenses": 0}
        if txn.category and txn.category.section and txn.category.section.name == 'Income':
            history[key]["income"] += txn.amount
        else:
            history[key]["expenses"] += txn.amount
    # Sort history by date
    history = dict(sorted(history.items(), key=lambda x: pd.to_datetime(x[0])))
    return history


@router.get("/range", summary="Get available transaction months")
def get_transactions_range(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Returns a list of months (YYYY-MM) for which there are transactions for the current user.
    """
    txns = db.query(Transaction).filter(Transaction.user_id == current_user["sub"]).all()
    months = {txn.date.strftime("%Y-%m") for txn in txns}
    return sorted(list(months), reverse=True)


@router.post("/update", summary="Update a transaction's category")
def update_transaction(update_request: UpdateTransactionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Update the category of a transaction.
    """
    txn = db.query(Transaction).filter(
        Transaction.id == update_request.transaction_id,
        Transaction.user_id == current_user["sub"]
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    # Look up the new category by name
    new_category = db.query(Category).filter(Category.name == update_request.category).first()
    if not new_category:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    txn.category_id = new_category.id
    db.commit()

    # Update Elasticsearch as well, if needed
    uploader = Uploader()
    uploader.post_df(pd.DataFrame([{
        'description': txn.description,
        'annotated_category': update_request.category
    }]))
    return get_transactions(db, current_user)


@router.delete("/{transaction_id}", summary="Delete a transaction")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Delete a transaction by ID.
    """
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user["sub"]
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    db.delete(txn)
    db.commit()
    logging.info(f"Transaction {transaction_id} deleted.")
    return get_transactions(db, current_user)
