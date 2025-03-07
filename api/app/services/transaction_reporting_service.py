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

logger = get_logger(__name__)
# Reporting / Aggregation Functions

def get_transactions_by_month_service(db: Session, current_user: dict, year: int, month: int):
    """
    Retrieve transactions for a specific month, grouped by section and category.

    :param db: Database session
    :param current_user: Current user information
    :param year: Year of the transactions
    :param month: Month of the transactions
    :return: Grouped transactions by section and category
    """
    logger.info(f"Fetching transactions for {year}-{month:02d} for user {current_user['sub']}")
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
        logger.info(f"Successfully fetched transactions for {year}-{month:02d}")
        return sorted_grouped
    except Exception as e:
        logger.error(f"Error fetching transactions for {year}-{month:02d}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching transactions")

def get_expense_totals_service(db: Session, current_user: dict, year: int, month: int):
    """
    Calculate total expenses for each category in a specific month.

    :param db: Database session
    :param current_user: Current user information
    :param year: Year of the transactions
    :param month: Month of the transactions
    :return: Dictionary with category names as keys and total expenses as values
    """
    logger.info(f"Calculating expense totals for {year}-{month:02d} for user {current_user['sub']}")
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
        totals = {category: total for category, total in results}
        logger.info(f"Successfully calculated expense totals for {year}-{month:02d}")
        return totals
    except Exception as e:
        logger.error(f"Error calculating expense totals for {year}-{month:02d}: {e}")
        raise HTTPException(status_code=500, detail="Error calculating expense totals")

def get_totals_service(db: Session, current_user: dict, year: int, month: int):
    """
    Calculate total income and expenses for a specific month.

    :param db: Database session
    :param current_user: Current user information
    :param year: Year of the transactions
    :param month: Month of the transactions
    :return: Dictionary with total income and expenses
    """
    logger.info(f"Calculating totals for {year}-{month:02d} for user {current_user['sub']}")
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
        income_total = totals.income if totals and totals.income else 0
        expenses_total = totals.expenses if totals and totals.expenses else 0
        logger.info(f"Successfully calculated totals for {year}-{month:02d}")
        return {"income": income_total, "expenses": expenses_total}
    except Exception as e:
        logger.error(f"Error calculating totals for {year}-{month:02d}: {e}")
        raise HTTPException(status_code=500, detail="Error calculating totals")

def get_grouped_transactions_service(db: Session, current_user: dict, year: int, month: int):
    """
    Retrieve and group transactions by section and category for a specific month.

    :param db: Database session
    :param current_user: Current user information
    :param year: Year of the transactions
    :param month: Month of the transactions
    :return: List of grouped transactions with totals
    """
    logger.info(f"Fetching and grouping transactions for {year}-{month:02d} for user {current_user['sub']}")
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)
    try:
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
        logger.info(f"Successfully fetched and grouped transactions for {year}-{month:02d}")
        return final_result
    except Exception as e:
        logger.error(f"Error fetching and grouping transactions for {year}-{month:02d}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching and grouping transactions")

def get_history_service(db: Session, current_user: dict):
    """
    Retrieve transaction history for the past six months.

    :param db: Database session
    :param current_user: Current user information
    :return: Dictionary with monthly income and expenses for the past six months
    """
    logger.info(f"Fetching transaction history for the past six months for user {current_user['sub']}")
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
        history = {}
        for txn, section_name in rows:
            key = txn.date.strftime("%B %Y")
            history.setdefault(key, {"income": 0, "expenses": 0})
            if section_name == 'Income':
                history[key]["income"] += txn.amount
            else:
                history[key]["expenses"] += txn.amount
        history = dict(sorted(history.items(), key=lambda x: pd.to_datetime(x[0])))
        logger.info("Successfully fetched transaction history")
        return history
    except Exception as e:
        logger.error(f"Error fetching transaction history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching transaction history")

def get_transactions_range_service(db: Session, current_user: dict):
    """
    Retrieve the range of months with transactions.

    :param db: Database session
    :param current_user: Current user information
    :return: List of months with transactions in 'YYYY-MM' format
    """
    logger.info(f"Fetching transaction range for user {current_user['sub']}")
    try:
        # Detect the dialect
        dialect = inspect(db.bind).dialect.name
        
        if (dialect == 'sqlite'):
            # SQLite-specific implementation
            results = (
                db.query(func.strftime('%Y-%m', Transaction.date))
                .filter(Transaction.is_deleted == 0)
                .distinct()
                .order_by(func.strftime('%Y-%m', Transaction.date).desc())
                .all()
            )
        else:
            # PostgreSQL and other databases implementation
            results = (
                db.query(
                    func.to_char(Transaction.date, 'YYYY-MM')
                )
                .filter(Transaction.is_deleted == 0)
                .distinct()
                .order_by(func.to_char(Transaction.date, 'YYYY-MM').desc())
                .all()
            )
        
        # Convert results to list of strings
        months = [row[0] for row in results]
        logger.info("Successfully fetched transaction range")
        return months
    except Exception as e:
        logger.error(f"Error in get_transactions_range_service: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving transaction range: {str(e)}")