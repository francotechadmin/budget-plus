# app/services/transaction_service.py
import calendar
import datetime
import logging
import io
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from fastapi import HTTPException
from app.models.models import Transaction, Category, Section, CategoryCorrections
from app.schemas.schemas import NewTransactionRequest, UpdateTransactionRequest
from app.transaction_categorization.model import predict_category

logger = logging.getLogger(__name__)

# CRUD Functions

def get_all_transactions(db: Session, current_user: dict):
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

def create_transaction(db: Session, current_user: dict, transaction: NewTransactionRequest):
    category = None
    if transaction.category:
        category = db.query(Category).filter(Category.name == transaction.category).first()
    if not category:
        predicted_category = predict_category(transaction.description)
        category = db.query(Category).filter(Category.name == predicted_category).first()
        if not category:
            category = db.query(Category).filter(Category.name == "Uncategorized").first()
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
        return new_transaction
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error adding transaction.")

def update_transaction_category(db: Session, current_user: dict, update_request: UpdateTransactionRequest):
    txn = db.query(Transaction).filter(
        Transaction.id == update_request.transaction_id,
        Transaction.user_id == current_user["sub"],
        Transaction.is_deleted == 0
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    new_category = db.query(Category).filter(Category.name == update_request.category).first()
    if not new_category:
        raise HTTPException(status_code=404, detail="Category not found.")
    correction = CategoryCorrections(
        user_id=current_user["sub"],
        transaction_id=txn.id,
        old_category_id=txn.category_id,
        new_category_id=new_category.id
    )
    db.add(correction)
    txn.category_id = new_category.id
    try:
        db.commit()
        updated_txn = db.query(Transaction).filter(
            Transaction.id == update_request.transaction_id,
            Transaction.user_id == current_user["sub"]
        ).first()
        return {
            "id": updated_txn.id,
            "description": updated_txn.description,
            "date": updated_txn.date,
            "amount": updated_txn.amount,
            "category": update_request.category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error recording category correction.")

def delete_transaction_by_id(db: Session, current_user: dict, transaction_id: int):
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user["sub"],
        Transaction.is_deleted == 0
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    txn.is_deleted = 1
    try:
        db.commit()
        return get_all_transactions(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting transaction.")

# Reporting / Aggregation Functions

def get_transactions_by_month_service(db: Session, current_user: dict, year: int, month: int):
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
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
    # Optionally place "Income" first if present
    if "Income" in grouped:
        sorted_grouped = {"Income": grouped.pop("Income")}
    else:
        sorted_grouped = {}
    for section in sorted(grouped):
        sorted_grouped[section] = grouped[section]
    return sorted_grouped

def get_expense_totals_service(db: Session, current_user: dict, year: int, month: int):
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)
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
    totals = {category: total for category, total in results}
    return totals

def get_totals_service(db: Session, current_user: dict, year: int, month: int):
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)
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
    income_total = totals.income if totals and totals.income else 0
    expenses_total = totals.expenses if totals and totals.expenses else 0
    return {"income": income_total, "expenses": expenses_total}

def get_grouped_transactions_service(db: Session, current_user: dict, year: int, month: int):
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)
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
    grouped = {}
    for txn, cat_name, sec_name in rows:
        grouped.setdefault(sec_name, {}).setdefault(cat_name, []).append({
            "id": txn.id,
            "description": txn.description,
            "date": txn.date.isoformat(),
            "amount": txn.amount,
            "category": cat_name,
            "section": sec_name
        })
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
    final_result.sort(key=lambda x: x["section"])
    return final_result

def get_history_service(db: Session, current_user: dict):
    six_months_ago = pd.to_datetime("today") - pd.DateOffset(months=6)
    six_months_ago = six_months_ago.replace(day=1)
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
    history = {}
    for txn, section_name in rows:
        key = txn.date.strftime("%B %Y")
        history.setdefault(key, {"income": 0, "expenses": 0})
        if section_name == 'Income':
            history[key]["income"] += txn.amount
        else:
            history[key]["expenses"] += txn.amount
    history = dict(sorted(history.items(), key=lambda x: pd.to_datetime(x[0])))
    return history

def get_transactions_range_service(db: Session, current_user: dict):
    subq = (
        db.query(func.to_char(Transaction.date, 'YYYY-MM').label("month"))
        .filter(
            Transaction.user_id == current_user["sub"],
            Transaction.is_deleted == 0,
        )
        .distinct()
        .subquery()
    )
    results = db.query(subq.c.month).order_by(subq.c.month.desc()).all()
    months = [row[0] for row in results]
    return months

# Import Transactions Service

from app.utils.file_parser import parse_transactions_file

async def import_transactions_service(file, db: Session, current_user: dict):
    df = await parse_transactions_file(file)

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
