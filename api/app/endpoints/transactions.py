# Import standard libraries
import calendar
import logging
import io
import datetime
import pandas as pd

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

# Import dependencies
from ..database.database import get_db
from ..models.models import Transaction, Category, Section, CategoryCorrections
from ..schemas.schemas import UpdateTransactionRequest, NewTransactionRequest

# Import authentication helper
from ..auth import get_current_user

# Import transaction categorization model
from app.transaction_categorization.model import predict_category

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
            .filter(
                Transaction.user_id == current_user["sub"], 
                Transaction.is_deleted == 0
            )
            .order_by(Transaction.date.desc())
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

@router.post("/", summary="Add a new transaction")
def add_transaction(
    transaction: NewTransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a new transaction for the current user.
    """
    logger.info(f"User {current_user['sub']} is adding a new transaction.")

    category = None
    
    # Look up the category by name
    if transaction.category:
        category = db.query(Category).filter(Category.name == transaction.category).first()
    
    if not category:
        # Use predict_category to determine the category
        predicted_category = predict_category(transaction.description)
        category = db.query(Category).filter(Category.name == predicted_category).first()
        if not category:
            logger.warning(f"Predicted category {predicted_category} not found. Defaulting to 'Uncategorized'.")
            category = db.query(Category).filter(Category.name == "Uncategorized").first()

    # Add transaction
    new_transaction = Transaction(
        user_id=current_user["sub"],
        description=transaction.description,
        date=transaction.date,
        amount=transaction.amount,
        category_id=category.id,
        is_manual=1,
    )
    db.add(new_transaction)

    try:
        db.commit()
        db.refresh(new_transaction)
        logger.info(f"Transaction added: {new_transaction.id}")

    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error adding transaction.")
    
    return new_transaction

@router.get("/{year}/{month}", summary="Get transactions for a specific month")
def get_transactions_by_month(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve transactions for a given month, grouped by section and category.
    """
    logger.info(f"User {current_user['sub']} requested transactions for {year}-{month:02d}.")
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    try:
        rows = (
            db.query(
                Section.name.label("section"),
                Category.name.label("category"),
                Transaction.id,
                Transaction.description,
                Transaction.date,
                Transaction.amount
            )
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Category.section_id == Section.id)
            .filter(
                Transaction.date.between(start_date, end_date),
                Transaction.user_id == current_user["sub"],
                Transaction.is_deleted == 0
            )
            .order_by(Section.name, Category.name, Transaction.date)
            .all()
        )
        logger.debug(f"Found {len(rows)} transactions for {year}-{month:02d} for user {current_user['sub']}.")
    except Exception as e:
        logger.error(f"Error retrieving transactions for {year}-{month:02d}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transactions for the specified month.")

    # Build nested grouping: { section: { category: [transactions...] } }
    grouped = {}
    for row in rows:
        section, category, txn_id, description, date, amount = row
        grouped.setdefault(section, {}).setdefault(category, []).append({
            "id": txn_id,
            "description": description,
            "date": date,
            "amount": amount,
            "category": category,
            "section": section
        })
    
    # Optionally, place "Income" first in the returned object.
    if "Income" in grouped:
        sorted_grouped = {"Income": grouped.pop("Income")}
    else:
        sorted_grouped = {}
    for section in sorted(grouped):
        sorted_grouped[section] = grouped[section]

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

    # Create date objects for start and end of the month.
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)

    try:
        results = (
            db.query(
                Category.name,
                func.sum(Transaction.amount).label("total_amount")
            )
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Category.section_id == Section.id)
            .filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.user_id == current_user["sub"],
                Section.name != 'Income',
                Category.name != 'Transfer',
                Transaction.is_deleted == 0
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
    
    # Create proper date objects for comparison
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)
    
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
            Transaction.user_id == current_user["sub"],
            Transaction.is_deleted == 0
        ).one_or_none()
        
        # If there are no transactions, totals will be None.
        if totals is None:
            income_total = 0
            expenses_total = 0
        else:
            income_total = totals.income or 0
            expenses_total = totals.expenses or 0
        
        logger.info(f"Income: {income_total}, Expenses: {expenses_total} for {year}-{month:02d}.")
        return {"income": income_total, "expenses": expenses_total}
    except Exception as e:
        logger.error(f"Error retrieving totals: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving totals.")


@router.get("/grouped/{year}/{month}", summary="Get grouped transactions for a specific month")
def get_grouped_transactions(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves transactions for the given month, grouped by section and category.
    Each group includes a computed total for that category and section.
    """
    logger.info(f"User {current_user['sub']} requested grouped transactions for {year}-{month:02d}.")

    try:
        # Convert to proper date objects
        start_date = datetime.date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime.date(year, month, last_day)
        
        # Retrieve all transactions for the period, joined with category and section names.
        rows = (
            db.query(
                Transaction,
                Category.name.label("category_name"),
                Section.name.label("section_name")
            )
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Category.section_id == Section.id)
            .filter(
                Transaction.date.between(start_date, end_date),
                Transaction.user_id == current_user["sub"],
                Transaction.is_deleted == 0
            )
            .order_by(Section.name, Category.name, Transaction.date)
            .all()
        )
    except Exception as e:
        logger.error(f"Error retrieving transactions grouped by month: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving grouped transactions for the specified month.")
    
    # Group transactions into a nested structure:
    grouped = {}
    for txn, cat_name, sec_name in rows:
        if sec_name not in grouped:
            grouped[sec_name] = {}
        if cat_name not in grouped[sec_name]:
            grouped[sec_name][cat_name] = []
        grouped[sec_name][cat_name].append({
            "id": txn.id,
            "description": txn.description,
            "date": txn.date.isoformat(),
            "amount": txn.amount,
            "category": cat_name,
            "section": sec_name
        })
    
    # Build final response with computed totals.
    final_result = []
    for sec_name, categories_data in grouped.items():
        section_total = 0
        category_list = []
        for cat_name, txns in categories_data.items():
            category_total = sum(txn["amount"] for txn in txns)
            section_total += category_total
            category_list.append({
                "name": cat_name,
                "total": category_total,
                "transactions": txns
            })
        final_result.append({
            "section": sec_name,
            "total": section_total,
            "categories": category_list
        })
    
    # Optionally sort final_result by section name.
    final_result.sort(key=lambda x: x["section"])
    logger.info(f"Returning grouped transactions for {year}-{month:02d}.")
    return final_result

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
            db.query(Transaction, Section.name)
            .join(Category, Transaction.category_id == Category.id)
            .join(Section, Section.id == Category.section_id)
            .filter(
                Transaction.date >= six_months_ago,
                Transaction.user_id == current_user["sub"],
                Transaction.is_deleted == 0,
            )
            .all()
        )
        logger.debug(f"Found {len(rows)} transactions in the last six months.")
    except Exception as e:
        logger.error(f"Error retrieving transaction history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transaction history.")
    
    history = {}
    for row in rows:
        txn, section_name = row
        key = txn.date.strftime("%B %Y")
        if key not in history:
            history[key] = {"income": 0, "expenses": 0}
        if section_name == 'Income':
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
    Uses a subquery to avoid PostgreSQL's DISTINCT/ORDER BY error.
    """
    logger.info(f"Retrieving transaction month range for user {current_user['sub']}.")
    try:
        # Create a subquery that selects distinct months.
        subq = (
            db.query(func.to_char(Transaction.date, 'YYYY-MM').label("month"))
            .filter(
                Transaction.user_id == current_user["sub"],
                Transaction.is_deleted == 0,
            )
            .distinct()
            .subquery()
        )
        # Order the distinct months from the subquery.
        results = db.query(subq.c.month).order_by(subq.c.month.desc()).all()
        months = [row[0] for row in results]
        logger.debug(f"Found transaction months: {months}")
    except Exception as e:
        logger.error(f"Error retrieving transaction range: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transaction range.")
    return months

@router.post("/update", summary="Update a transaction's category")
def update_transaction(
    update_request: UpdateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update the category of a transaction and, if requested, index the updated transaction in Elasticsearch.
    """
    logger.info(f"User {current_user['sub']} requested update for transaction {update_request.transaction_id}.")
    txn = db.query(Transaction).filter(
        Transaction.id == update_request.transaction_id,
        Transaction.user_id == current_user["sub"],
        Transaction.is_deleted == 0
    ).first()
    if not txn:
        logger.warning(f"Transaction {update_request.transaction_id} not found for user {current_user['sub']}.")
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    # Look up the new category by name.
    new_category = db.query(Category).filter(Category.name == update_request.category).first()
    if not new_category:
        logger.warning(f"Category {update_request.category} not found for update request.")
        raise HTTPException(status_code=404, detail="Category not found.")
        
    #Update the transaction's category in the CategoryCorrections table.
    correction = CategoryCorrections(
        user_id=current_user["sub"],
        transaction_id=txn.id,
        old_category_id=txn.category_id,
        new_category_id=new_category.id
    )
    db.add(correction)

    # Update the transaction's category.
    txn.category_id = new_category.id
 
    try:
        db.commit()
        logger.info(f"Category correction recorded for transaction {txn.id}.")
    except Exception as e:
        logger.error(f"Error recording category correction: {e}")
        raise HTTPException(status_code=500, detail="Error recording category correction.")
        
    # Return updated transaction 
    updated_txn = db.query(Transaction).filter(
        Transaction.id == update_request.transaction_id,
        Transaction.user_id == current_user["sub"]
    ).first()
    if not updated_txn:
        logger.warning(f"Transaction {update_request.transaction_id} not found after update.")
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    response = {
        "id": updated_txn.id,
        "description": updated_txn.description,
        "date": updated_txn.date,
        "amount": updated_txn.amount,
        "category": update_request.category
    }
    logger.info(f"Returning updated transaction {update_request.transaction_id}.")
    return response

@router.delete("/{transaction_id}", summary="Delete a transaction")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Delete a transaction by ID.
    """
    logger.info(f"User {current_user['sub']} requested deletion of transaction {transaction_id}.")
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user["sub"],
        Transaction.is_deleted == 0
    ).first()
    if not txn:
        logger.warning(f"Transaction {transaction_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    # Mark the transaction as deleted.
    txn.is_deleted = 1
    try:
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

    **Optional column:**
        - category (if provided, will override the predicted category)

    Elasticsearch is only used if no valid category is provided in the file.
    If ES is available but the file provides a valid category, that value is used.
    If the provided category is not found in the DB, the transaction is categorized as "Uncategorized".
    """
    logger.info(f"User {current_user['sub']} is importing transactions from file: {file.filename}")
    new_transactions = []
    required_columns = {"date", "description", "amount"}
    
    # Determine file type by extension and read file into DataFrame.
    file_ext = file.filename.lower()
    try:
        contents = await file.read()
        if file_ext.endswith(".csv"):
            logger.debug("Reading CSV file content.")
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        elif file_ext.endswith((".xlsx", ".xls")):
            logger.debug("Reading Excel file content.")
            df = pd.read_excel(io.BytesIO(contents))
        else:
            logger.warning(f"Unsupported file format for file: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload a CSV or Excel file."
            )
    except Exception as e:
        logger.error(f"Error reading file {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Verify that the DataFrame contains all required columns.
    if not required_columns.issubset(set(df.columns)):
        missing = required_columns - set(df.columns)
        logger.warning(f"File {file.filename} is missing required columns: {', '.join(missing)}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing)}"
        )
    logger.debug(f"File {file.filename} contains all required columns.")

    # Pre-fetch categories for the current user.
    categories_db = db.query(Category).filter(Category.user_id == current_user["sub"]).all()
    # Build a lookup dictionary using lower-case keys.
    categories_dict = {cat.name.lower(): cat for cat in categories_db}
    
    # Pre-fetch existing transactions in the file's date range to avoid duplicate checks per row.
    try:
        # Convert file date column to datetime if not already.
        df['date'] = pd.to_datetime(df['date']).dt.date
    except Exception as e:
        logger.error(f"Error converting date column: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format in file.")

    min_date = df['date'].min()
    max_date = df['date'].max()
    existing_txns = db.query(Transaction).filter(
        Transaction.user_id == current_user["sub"],
        Transaction.date.between(min_date, max_date)
    ).all()
    # Build a set of keys for quick duplicate lookup.
    existing_keys = set((txn.description, txn.date, txn.amount, txn.category_id) for txn in existing_txns)

    # Process each row of the DataFrame.
    for idx, row in df.iterrows():
        # Skip rows with missing required fields.
        if pd.isna(row['date']) or pd.isna(row['description']) or pd.isna(row['amount']):
            logger.warning(f"Row {idx} is missing required fields. Skipping.")
            continue

        logger.debug(f"Processing row {idx} of file {file.filename}.")
        
        # Determine the final category.
        file_category = row.get('category', None)
        if file_category:
            final_category = file_category
            logger.debug(f"Row {idx}: Using provided category: {final_category}")
        else:
            # Use Predictor to get category.
            predicted_category = predict_category(row['description'])
            logger.debug(f"Row {idx}: Predicted category: {predicted_category}")

            # If the predicted category is valid, use it.
            # If not, default to "Uncategorized".
            if predicted_category.lower() in categories_dict:
                final_category = predicted_category
                logger.debug(f"Row {idx}: Using predicted category: {final_category}")
            else:
                final_category = "Uncategorized"
                logger.warning(f"Row {idx}: No valid category found. Defaulting to 'Uncategorized'.")
        
        # Look up the category in our pre-fetched dictionary.
        cat_entry = categories_dict.get(final_category.lower())
        if not cat_entry:
            logger.warning(f"Category '{final_category}' not found for row {idx}. Using 'Uncategorized'.")
            cat_entry = categories_dict.get("Uncategorized")
            if not cat_entry:
                logger.info("Creating default 'Uncategorized' category.")
                cat_entry = Category(
                    user_id=current_user["sub"],
                    section_id=None,  # Adjust if you want to assign a default section
                    name="Uncategorized",
                    description="Fallback category when no match is found"
                )
                db.add(cat_entry)
                db.commit()
                db.refresh(cat_entry)
                # Add to our dictionary for subsequent lookups.
                categories_dict["Uncategorized"] = cat_entry
        
        # Build a duplicate key for this transaction.
        txn_key = (row['description'], row['date'], row['amount'], cat_entry.id)
        if txn_key in existing_keys:
            logger.debug(f"Duplicate transaction found for row {idx}. Skipping.")
            continue

        # Add the new key so that subsequent rows in the file are compared.
        existing_keys.add(txn_key)

        # Create a new Transaction record.
        new_txn = Transaction(
            user_id=current_user["sub"],
            description=row['description'],
            date=row['date'],
            amount=row['amount'],
            category_id=cat_entry.id,
            is_imported=1,
        )
        new_transactions.append(new_txn)
        logger.debug(f"Row {idx} processed: Transaction added.")

    # Bulk insert new transactions.
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
    
    from .transactions import get_transactions  
    return get_transactions(db, current_user)
