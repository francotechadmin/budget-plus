# Import standard libraries
import calendar
import logging
import io
import pandas as pd

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

# Import dependencies
from ..database.database import get_db
from ..models.models import Transaction, Category, Section
from ..schemas.schemas import UpdateTransactionRequest

# Import Elasticsearch helper classes
from ..elasticsearch_simple_client.uploader import Uploader
from ..elasticsearch_simple_client.searcher import Searcher

# Import authentication helper
from ..auth import get_current_user

# Set up logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", summary="Get all transactions")
def get_transactions(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve all transactions for the current user.
    Joins the Transaction, Category, and Section tables to return human-readable names.
    """
    logger.info(f"User {current_user['sub']} is retrieving all transactions.")
    try:
        txns = (
            db.query(Transaction, Category.name.label("category_name"), Section.name.label("section_name"))
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Category.section_id == Section.id)
            .filter(Transaction.user_id == current_user["sub"])
            .all()
        )
        logger.debug(f"Fetched {len(txns)} transactions for user {current_user['sub']}.")
    except Exception as e:
        logger.error(f"Error fetching transactions for user {current_user['sub']}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transactions.")
    
    response = [
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
    logger.info(f"Returning {len(response)} transactions for user {current_user['sub']}.")
    return response

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
    logger.info(f"User {current_user['sub']} is uploading {len(files)} file(s).")
    
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
        logger.info(f"Processing file: {file.filename}")
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
                logger.warning(f"File {file.filename} has unsupported format.")
                raise HTTPException(status_code=400, detail="Unsupported file format.")
            logger.debug(f"Determined file source as {source} for file {file.filename}.")
        except Exception as e:
            logger.error(f"Failed to process file preview for {file.filename}: {e}")
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
            logger.debug(f"File {file.filename} processed successfully with {len(df)} rows.")
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
        
        for idx, row in df.iterrows():
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
                logger.debug(f"Duplicate transaction found for row {idx} in file {file.filename}. Skipping.")
                continue

            # Use the searcher to determine the annotated category from the transaction description.
            try:
                es_result = searcher.execute_search(
                    field="description",
                    shoulds=[row['description']]
                )["hits"]["hits"]
                annotated_category = es_result[0]["_source"]["annotated_category"] if es_result else "Uncategorized"
            except Exception as e:
                logger.error(f"Error during Elasticsearch search for row {idx}: {e}")
                annotated_category = "Uncategorized"
            
            # Look up the Category in our database by name
            cat_entry = db.query(Category).filter(Category.name == annotated_category).first()
            if not cat_entry:
                logger.warning(f"Category {annotated_category} not found for row {idx}. Falling back to 'Uncategorized'.")
                cat_entry = db.query(Category).filter(Category.name == "Uncategorized").first()
                if not cat_entry:
                    logger.error("No valid 'Uncategorized' category found in the database.")
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
            logger.debug(f"Prepared new transaction for row {idx} in file {file.filename}.")
        
    if new_transactions:
        try:
            db.bulk_save_objects(new_transactions)
            db.commit()
            logger.info(f"Inserted {len(new_transactions)} new transactions for user {current_user['sub']}.")
        except Exception as e:
            logger.error(f"Error inserting transactions: {e}")
            raise HTTPException(status_code=500, detail="Error saving transactions.")
    else:
        logger.info("No new transactions to insert.")
    
    return get_transactions(db, current_user)

@router.get("/{year}/{month}", summary="Get transactions for a specific month")
def get_transactions_by_month(year: int, month: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Retrieve transactions for a given month, grouped by section and category.
    """
    logger.info(f"User {current_user['sub']} requested transactions for {year}-{month:02d}.")
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    try:
        rows = (
            db.query(Transaction, Category.name, Section.name)
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Category.section_id == Section.id)
            .filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.user_id == current_user["sub"]
            )
            .all()
        )
        logger.debug(f"Found {len(rows)} transactions for {year}-{month:02d} for user {current_user['sub']}.")
    except Exception as e:
        logger.error(f"Error retrieving transactions by month: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transactions for the specified month.")
    
    grouped = {}
    for row in rows:
        txn, category_name, section_name = row
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
    logger.info(f"Returning grouped transactions for {year}-{month:02d}.")
    return sorted_grouped

@router.get("/expenses/{year}/{month}", summary="Get expense totals for a month")
def get_transactions_expenses(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate expense totals for a specific month.
    Excludes transactions in the 'Income' section or 'Transfer' category.
    """
    logger.info(f"Calculating expense totals for user {current_user['sub']} for {year}-{month:02d}.")
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"

    try:
        results = (
            db.query(
                Category.name,
                func.sum(Transaction.amount).label("total_amount")
            )
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Category.section_id == Section.id)
            .filter(
                Transaction.date.between(start_date, end_date),
                Transaction.user_id == current_user["sub"],
                Section.name != 'Income',
                Category.name != 'Transfer'
            )
            .group_by(Category.name)
            .all()
        )
        logger.debug(f"Expense totals query returned {len(results)} rows.")
    except Exception as e:
        logger.error(f"Error retrieving expense transactions: {e}")
        raise HTTPException(status_code=500, detail="Error calculating expenses.")

    totals = {category: total for category, total in results}
    logger.info(f"Returning expense totals for {year}-{month:02d}.")
    return totals

@router.get("/totals/{year}/{month}", summary="Get income and expenses totals for a month")
def get_transactions_totals(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the total income and total expenses for the specified month.
    Income is determined by transactions whose category's section is 'Income';
    all other transactions are treated as expenses.
    """
    logger.info(f"Calculating totals for user {current_user['sub']} for {year}-{month:02d}.")
    
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    try:
        totals = db.query(
            func.sum(
                case(
                    (Section.name == 'Income', Transaction.amount),
                    else_=0
                )
            ).label("income"),
            func.sum(
                case(
                    (Section.name != 'Income', Transaction.amount),
                    else_=0
                )
            ).label("expenses")
        ).join(Category, Transaction.category_id == Category.id
        ).join(Section, Category.section_id == Section.id
        ).filter(
            Transaction.date.between(start_date, end_date),
            Transaction.user_id == current_user["sub"]
        ).one()
        
        income_total = totals.income or 0
        expenses_total = totals.expenses or 0
        logger.info(f"Income: {income_total}, Expenses: {expenses_total} for {year}-{month:02d}.")
        return {"income": income_total, "expenses": expenses_total}
    except Exception as e:
        logger.error(f"Error retrieving totals: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving totals.")


@router.get("/history", summary="Get transaction history for the last six months")
def get_transactions_history(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Returns a history of transactions aggregated by month for the last six months.
    """
    logger.info(f"User {current_user['sub']} is retrieving transaction history for the last six months.")
    six_months_ago = pd.to_datetime("today") - pd.DateOffset(months=6)
    six_months_ago = six_months_ago.replace(day=1)
    
    try:
        rows = (
            db.query(Transaction, Category.name, Section.name)
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Transaction.category_id == Category.id)
            .filter(
                Transaction.date >= six_months_ago,
                Transaction.user_id == current_user["sub"],
                Category.name != 'Transfer'
            )
            .all()
        )
        logger.debug(f"Found {len(rows)} transactions in the last six months.")
    except Exception as e:
        logger.error(f"Error retrieving transaction history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transaction history.")
    
    history = {}
    for row in rows:
        txn, category_name, section_name = row
        key = txn.date.strftime("%B %Y")
        if key not in history:
            history[key] = {"income": 0, "expenses": 0}
        if category_name and section_name and section_name == 'Income':
            history[key]["income"] += txn.amount
        else:
            history[key]["expenses"] += txn.amount
    # Sort history by date
    history = dict(sorted(history.items(), key=lambda x: pd.to_datetime(x[0])))
    logger.info("Returning transaction history.")
    return history

@router.get("/range", summary="Get available transaction months")
def get_transactions_range(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns a list of months (YYYY-MM) for which there are transactions for the current user.
    """
    logger.info(f"Retrieving transaction month range for user {current_user['sub']}.")
    try:
        results = (
            db.query(func.distinct(func.to_char(Transaction.date, 'YYYY-MM')))
            .filter(Transaction.user_id == current_user["sub"])
            .order_by(func.to_char(Transaction.date, 'YYYY-MM').desc())
            .all()
        )
        months = [row[0] for row in results]
        logger.debug(f"Found transaction months: {months}")
    except Exception as e:
        logger.error(f"Error retrieving transaction range: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transaction range.")
    return months

@router.post("/update", summary="Update a transaction's category")
def update_transaction(update_request: UpdateTransactionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Update the category of a transaction.
    """
    logger.info(f"User {current_user['sub']} requested update for transaction {update_request.transaction_id}.")
    txn = db.query(Transaction).filter(
        Transaction.id == update_request.transaction_id,
        Transaction.user_id == current_user["sub"]
    ).first()
    if not txn:
        logger.warning(f"Transaction {update_request.transaction_id} not found for user {current_user['sub']}.")
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    # Look up the new category by name
    new_category = db.query(Category).filter(Category.name == update_request.category).first()
    if not new_category:
        logger.warning(f"Category {update_request.category} not found for update request.")
        raise HTTPException(status_code=404, detail="Category not found.")
    
    txn.category_id = new_category.id
    try:
        db.commit()
        logger.info(f"Transaction {update_request.transaction_id} updated to category {update_request.category}.")
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail="Error updating transaction.")
    
    # Update Elasticsearch as well, if needed
    try:
        uploader = Uploader()
        uploader.post_df(pd.DataFrame([{
            'description': txn.description,
            'annotated_category': update_request.category
        }]))
        logger.debug("Elasticsearch updated for transaction change.")
    except Exception as e:
        logger.error(f"Error updating Elasticsearch: {e}")
    
    return get_transactions(db, current_user)

@router.delete("/{transaction_id}", summary="Delete a transaction")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Delete a transaction by ID.
    """
    logger.info(f"User {current_user['sub']} requested deletion of transaction {transaction_id}.")
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user["sub"]
    ).first()
    if not txn:
        logger.warning(f"Transaction {transaction_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    try:
        db.delete(txn)
        db.commit()
        logger.info(f"Transaction {transaction_id} deleted for user {current_user['sub']}.")
    except Exception as e:
        logger.error(f"Error deleting transaction {transaction_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting transaction.")
    
    return get_transactions(db, current_user)

@router.post("/import", summary="Upload bank transactions in bulk (standard format)")
async def import_bank_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Bulk import transactions using a standardized CSV or Excel file.
    
    **Required columns:** 
      - date
      - description
      - amount
      - category
    
    The endpoint uses the file extension to determine how to read the file.
    """
    logger.info(f"User {current_user['sub']} is importing transactions from file: {file.filename}")
    new_transactions = []
    required_columns = {"date", "description", "amount", "category"}
    
    # Determine file type by extension
    file_ext = file.filename.lower()
    if file_ext.endswith(".csv"):
        try:
            contents = await file.read()
            logger.debug("Reading CSV file content.")
            # Decode CSV content (assuming UTF-8) and wrap in StringIO
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        except Exception as e:
            logger.error(f"Error reading CSV file {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Error reading CSV file: {str(e)}")
    elif file_ext.endswith((".xlsx", ".xls")):
        try:
            contents = await file.read()
            logger.debug("Reading Excel file content.")
            # Wrap the bytes in BytesIO for Excel
            df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            logger.error(f"Error reading Excel file {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Error reading Excel file: {str(e)}")
    else:
        logger.warning(f"Unsupported file format for file: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a CSV or Excel file."
        )
    
    # Verify that the DataFrame contains all required columns
    if not required_columns.issubset(set(df.columns)):
        missing = required_columns - set(df.columns)
        logger.warning(f"File {file.filename} is missing required columns: {', '.join(missing)}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing)}"
        )
    logger.debug(f"File {file.filename} contains all required columns.")
    
    # Process each row of the DataFrame
    for idx, row in df.iterrows():
        logger.debug(f"Processing row {idx} of file {file.filename}.")
        # Lookup the category for the current user by name
        cat_entry = (
            db.query(Category)
            .filter(Category.name == row['category'], Category.user_id == current_user["sub"])
            .first()
        )
        if not cat_entry:
            logger.warning(f"Category {row['category']} not found for row {idx}. Trying 'Uncategorized'.")
            cat_entry = (
                db.query(Category)
                .filter(Category.name == "Uncategorized", Category.user_id == current_user["sub"])
                .first()
            )
            if not cat_entry:
                logger.info("Creating default 'Uncategorized' category.")
                cat_entry = Category(
                    user_id=current_user["sub"],
                    section_id=None,  # Adjust if you want to assign a default section
                    name="Uncategorized",
                    description="Default uncategorized transactions"
                )
                db.add(cat_entry)
                db.commit()
                db.refresh(cat_entry)
        
        # Check for duplicate transactions by matching description, date, amount, and category
        existing_txn = (
            db.query(Transaction)
            .filter(
                Transaction.description == row['description'],
                Transaction.date == row['date'],
                Transaction.amount == row['amount'],
                Transaction.category_id == cat_entry.id,
                Transaction.user_id == current_user["sub"]
            )
            .first()
        )
        if existing_txn:
            logger.debug(f"Duplicate transaction found for row {idx}. Skipping.")
            continue
        
        # Create a new Transaction record
        new_txn = Transaction(
            user_id=current_user["sub"],
            description=row['description'],
            date=row['date'],
            amount=row['amount'],
            category_id=cat_entry.id
        )
        new_transactions.append(new_txn)
        logger.debug(f"Row {idx} processed: Transaction added.")
    
    if new_transactions:
        try:
            db.bulk_save_objects(new_transactions)
            db.commit()
            logger.info(f"Inserted {len(new_transactions)} new transactions from import for user {current_user['sub']}.")
        except Exception as e:
            logger.error(f"Error inserting imported transactions: {e}")
            raise HTTPException(status_code=500, detail="Error saving imported transactions.")
    else:
        logger.info("No new transactions were found in the import file.")
    
    # Return updated transactions for the current user.
    from .transactions import get_transactions  
    return get_transactions(db, current_user)
