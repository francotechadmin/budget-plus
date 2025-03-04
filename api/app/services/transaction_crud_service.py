# app/services/transaction_service.py
from ..utils.logger import get_logger
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Transaction, Category, Section, CategoryCorrections
from app.schemas.schemas import NewTransactionRequest, UpdateTransactionRequest
from app.transaction_categorization.model import predict_category

logger = get_logger(__name__)
# CRUD Functions

def get_all_transactions(db: Session, current_user: dict):
    """
    Retrieve all transactions for the current user.

    Args:
        db (Session): Database session.
        current_user (dict): Dictionary containing current user information.

    Returns:
        list: List of transactions with their details.
    """
    logger.info("Retrieving all transactions for user: %s", current_user["sub"])
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
        logger.info("Transactions retrieved successfully for user: %s", current_user["sub"])
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
    except Exception as e:
        logger.error("Error retrieving transactions for user: %s, error: %s", current_user["sub"], str(e))
        raise HTTPException(status_code=500, detail="Error retrieving transactions.")

def create_transaction(db: Session, current_user: dict, transaction: NewTransactionRequest):
    """
    Create a new transaction for the current user.

    Args:
        db (Session): Database session.
        current_user (dict): Dictionary containing current user information.
        transaction (NewTransactionRequest): New transaction request schema.

    Returns:
        Transaction: The created transaction object.
    """
    logger.info("Creating a new transaction for user: %s", current_user["sub"])
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
        logger.info("Transaction created successfully for user: %s", current_user["sub"])
        return new_transaction
    except Exception as e:
        db.rollback()
        logger.error("Error adding transaction for user: %s, error: %s", current_user["sub"], str(e))
        raise HTTPException(status_code=500, detail="Error adding transaction.")

def update_transaction_category(db: Session, current_user: dict, update_request: UpdateTransactionRequest):
    """
    Update the category of an existing transaction for the current user.

    Args:
        db (Session): Database session.
        current_user (dict): Dictionary containing current user information.
        update_request (UpdateTransactionRequest): Update transaction request schema.

    Returns:
        dict: Updated transaction details.
    """
    logger.info("Updating transaction category for user: %s, transaction_id: %s", current_user["sub"], update_request.transaction_id)
    txn = db.query(Transaction).filter(
        Transaction.id == update_request.transaction_id,
        Transaction.user_id == current_user["sub"],
        Transaction.is_deleted == 0
    ).first()
    if not txn:
        logger.warning("Transaction not found for user: %s, transaction_id: %s", current_user["sub"], update_request.transaction_id)
        raise HTTPException(status_code=404, detail="Transaction not found.")
    new_category = db.query(Category).filter(Category.name == update_request.category).first()
    if not new_category:
        logger.warning("Category not found for user: %s, category: %s", current_user["sub"], update_request.category)
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
        logger.info("Transaction category updated successfully for user: %s, transaction_id: %s", current_user["sub"], update_request.transaction_id)
        return {
            "id": updated_txn.id,
            "description": updated_txn.description,
            "date": updated_txn.date,
            "amount": updated_txn.amount,
            "category": update_request.category
        }
    except Exception as e:
        logger.error("Error recording category correction for user: %s, transaction_id: %s, error: %s", current_user["sub"], update_request.transaction_id, str(e))
        raise HTTPException(status_code=500, detail="Error recording category correction.")

def delete_transaction_by_id(db: Session, current_user: dict, transaction_id: int):
    """
    Delete a transaction by its ID for the current user.

    Args:
        db (Session): Database session.
        current_user (dict): Dictionary containing current user information.
        transaction_id (int): ID of the transaction to be deleted.

    Returns:
        list: List of remaining transactions after deletion.
    """
    logger.info("Deleting transaction for user: %s, transaction_id: %s", current_user["sub"], transaction_id)
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user["sub"],
        Transaction.is_deleted == 0
    ).first()
    if not txn:
        logger.warning("Transaction not found for user: %s, transaction_id: %s", current_user["sub"], transaction_id)
        raise HTTPException(status_code=404, detail="Transaction not found.")
    txn.is_deleted = 1
    try:
        db.commit()
        logger.info("Transaction deleted successfully for user: %s, transaction_id: %s", current_user["sub"], transaction_id)
        return get_all_transactions(db, current_user)
    except Exception as e:
        logger.error("Error deleting transaction for user: %s, transaction_id: %s, error: %s", current_user["sub"], transaction_id, str(e))
        raise HTTPException(status_code=500, detail="Error deleting transaction.")
