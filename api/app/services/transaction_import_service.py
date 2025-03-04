# app/services/transaction_service.py
import calendar
import datetime
from ..utils.logger import get_logger
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, case, inspect
from fastapi import HTTPException
from app.models.models import Transaction, Category, Section, CategoryCorrections
from app.schemas.schemas import NewTransactionRequest, UpdateTransactionRequest
from app.categorization.model import predict_category
from app.utils.file_parser import parse_transactions_file

logger = get_logger(__name__)
async def import_transactions_service(file, db: Session, current_user: dict):
    try:
        df = await parse_transactions_file(file)
    except HTTPException as e:
        logger.error(f"Error parsing file: {e.detail}")
        raise e

    new_transactions = []
    # Pre-fetch categories for the current user.
    categories_db = db.query(Category).filter(Category.user_id == current_user["sub"]).all()
    # Build a lookup dictionary using lower-case keys.
    categories_dict = {cat.name.lower(): cat for cat in categories_db}

    # Determine the date range in the file.
    min_date = df['date'].min()
    max_date = df['date'].max()

    # Pre-fetch counts of existing transactions from the DB in this date range.
    db_txns = db.query(
        Transaction.description,
        Transaction.date,
        Transaction.amount,
        Transaction.category_id,
        func.count(Transaction.id).label("count")
    ).filter(
        Transaction.user_id == current_user["sub"],
        Transaction.date.between(min_date, max_date),
        Transaction.is_deleted == 0,
    ).group_by(
        Transaction.description,
        Transaction.date,
        Transaction.amount,
        Transaction.category_id
    ).all()

    # Build a lookup dictionary: key -> count
    db_counts = {}
    for desc, d, amt, cat_id, count in db_txns:
        key = (desc, d, amt, cat_id)
        db_counts[key] = count

    # Dictionary to count occurrences within the file.
    file_counts = {}

    # Process each row of the DataFrame.
    for idx, row in df.iterrows():
        # Skip rows with missing required fields.
        if pd.isna(row['date']) or pd.isna(row['description']) or pd.isna(row['amount']):
            logger.warning(f"Row {idx} is missing required fields. Skipping.")
            continue

        logger.debug(f"Processing row {idx} of file {file.filename}.")
        
        # Determine the final category.
        file_category = row.get('category', None)
        # check file category is a valid string
        if file_category and isinstance(file_category, str) and file_category.strip().lower() in categories_dict:
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
        file_counts[txn_key] = file_counts.get(txn_key, 0) + 1

        # Compare file count to DB count.
        db_count = db_counts.get(txn_key, 0)
        if file_counts[txn_key] <= db_count:
            logger.debug(f"Row {idx}: Duplicate detected (file count {file_counts[txn_key]}, DB count {db_count}). Skipping.")
            continue

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

    if new_transactions:
        try:
            db.bulk_save_objects(new_transactions)
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error saving imported transactions.")
    return {"detail": "Transactions imported successfully."}
