import io
import calendar
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.database import get_db
from ..models.models import Transaction, Category
from ..schemas.schemas import UpdateTransactionRequest

# Import Elasticsearch helper classes
from ..elasticsearch_simple_client.uploader import Uploader
from ..elasticsearch_simple_client.searcher import Searcher

# Import authentication helper
from ..auth import get_current_user

router = APIRouter()


@router.post("/", summary="Upload bank transactions")
async def upload_bank_transactions(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    """
    Upload bank transactions via CSV files.
    The endpoint detects the source (e.g. Chase or Citi) based on column names
    and processes the file accordingly.
    """
    logging.info(f"Uploading {len(files)} file(s)...")
    
    # Expected columns for each bank format
    chase_debit_columns = ['Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance', 'Check or Slip #']
    chase_credit_columns = ['Transaction Date', 'Post Date', 'Description', 'Category', 'Type', 'Amount', 'Memo']
    citi_columns = ['Status', 'Date', 'Description', 'Debit', 'Credit']

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
                df['amount'] = df['Debit'].fillna(0) * -1 + df['Credit'].fillna(0) * -1
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
        
        new_transactions = []
        searcher = Searcher()
        for _, row in df.iterrows():
            # Check for duplicates by matching description, date, and amount
            existing_txn = db.query(Transaction).filter(
                and_(
                    Transaction.description == row['description'],
                    Transaction.date == row['date'],
                    Transaction.amount == row['amount']
                )
            ).first()
            if not existing_txn:
                es_result = searcher.execute_search(
                    field="description",
                    shoulds=[row['description']]
                )["hits"]["hits"]
                annotated_category = es_result[0]["_source"]["annotated_category"] if es_result else "Uncategorized"
                # Get section from Category table
                cat_entry = db.query(Category).filter(Category.category == annotated_category).first()
                section = cat_entry.section if cat_entry else "Uncategorized"
                new_txn = Transaction(
                    description=row['description'],
                    date=row['date'],
                    amount=row['amount'],
                    category=annotated_category,
                    section=section
                )
                new_transactions.append(new_txn)
        
        if new_transactions:
            db.bulk_save_objects(new_transactions)
            db.commit()
            logging.info(f"Inserted {len(new_transactions)} new transactions.")
        else:
            logging.info("No new transactions to insert.")

    return get_transactions(db)


@router.get("/", summary="Get all transactions")
def get_transactions(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    txns = db.query(Transaction).all()
    # Sort transactions by date and description (newest first)
    txns = sorted(txns, key=lambda x: (x.date, x.description), reverse=True)
    return txns


@router.get("/{year}/{month}", summary="Get transactions for a specific month")
def get_transactions_by_month(year: int, month: int, db: Session = Depends(get_db)):
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    txns = db.query(Transaction).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
    ).all()

    grouped = {}
    for txn in txns:
        grouped.setdefault(txn.section, {}).setdefault(txn.category, []).append(txn)
    
    # Optionally, move the "Income" section to the top
    sorted_grouped = {}
    if "Income" in grouped:
        sorted_grouped["Income"] = grouped.pop("Income")
    for section, cats in sorted(grouped.items()):
        sorted_grouped[section] = cats
    return sorted_grouped


@router.get("/expenses/{year}/{month}", summary="Get expense totals for a month")
def get_transactions_expenses(year: int, month: int, db: Session = Depends(get_db)):
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    txns = db.query(Transaction).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.section != 'Income',
        Transaction.category != 'Transfer',
    ).all()

    totals = {}
    for txn in txns:
        totals.setdefault(txn.category, 0)
        totals[txn.category] += txn.amount
    return totals


@router.get("/totals/{year}/{month}", summary="Get income and expenses totals for a month")
def get_transactions_totals(year: int, month: int, db: Session = Depends(get_db)):
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    txns = db.query(Transaction).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    income_total = sum(txn.amount for txn in txns if txn.section == 'Income')
    expenses_total = sum(txn.amount for txn in txns if txn.section != 'Income')
    return {"income": income_total, "expenses": expenses_total}


@router.get("/history", summary="Get transaction history for the last six months")
def get_transactions_history(db: Session = Depends(get_db)):
    six_months_ago = pd.to_datetime("today") - pd.DateOffset(months=6)
    six_months_ago = six_months_ago.replace(day=1)
    txns = db.query(Transaction).filter(
        Transaction.date >= six_months_ago,
        Transaction.category != 'Transfer'
    ).all()

    history = {}
    for txn in txns:
        key = txn.date.strftime("%B %Y")
        if key not in history:
            history[key] = {"income": 0, "expenses": 0}
        if txn.section == 'Income':
            history[key]["income"] += txn.amount
        else:
            history[key]["expenses"] += txn.amount
    history = dict(sorted(history.items(), key=lambda x: pd.to_datetime(x[0])))
    return history


@router.get("/range", summary="Get available transaction months")
def get_transactions_range(db: Session = Depends(get_db)):
    txns = db.query(Transaction).all()
    months = {txn.date.strftime("%Y-%m") for txn in txns}
    return sorted(list(months), reverse=True)


@router.post("/update", summary="Update a transaction's category")
def update_transaction(update_request: UpdateTransactionRequest, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == update_request.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    txn.category = update_request.category
    cat_entry = db.query(Category).filter(Category.category == update_request.category).first()
    if cat_entry:
        txn.section = cat_entry.section
    db.commit()

    # Update the change in Elasticsearch as well
    uploader = Uploader()
    uploader.post_df(pd.DataFrame([{
        'description': txn.description,
        'annotated_category': update_request.category
    }]))
    return get_transactions(db)


@router.delete("/{transaction_id}", summary="Delete a transaction")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    db.delete(txn)
    db.commit()
    logging.info(f"Transaction {transaction_id} deleted.")
    return get_transactions(db)
