# app/endpoints/transactions_crud.py
from ..utils.logger import get_logger
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.transaction_crud_service import (
    get_all_transactions,
    create_transaction,
    update_transaction_category,
    delete_transaction_by_id,
)
from app.database.database import get_db
from app.auth import get_current_user
from app.schemas.schemas import NewTransactionRequest, UpdateTransactionRequest

# Configure logging
logger = get_logger(__name__)
router = APIRouter()

@router.get("/", summary="Get all transactions")
def get_transactions(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Retrieve all transactions for the current user.

    :param db (Session): Database session dependency.
    :param current_user (dict): Current authenticated user dependency.
    :return List[Transaction]: List of transactions for the current user.
    :raises HTTPException: If there is an error retrieving transactions.
    :rtype: List[Transaction]
    """
    try:
        transactions = get_all_transactions(db, current_user)
        logger.info(f"Retrieved transactions for user {current_user['id']}")
        return transactions
    except Exception as e:
        logger.error(f"Error retrieving transactions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transactions.")

@router.post("/", summary="Add a new transaction")
def add_transaction(
    transaction: NewTransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a new transaction for the current user.

    :param transaction (NewTransactionRequest): Transaction data.
    :param db (Session): Database session dependency.
    :param current_user (dict): Current authenticated user dependency.
    :return Transaction: The newly created transaction.
    :raises HTTPException: If there is an error adding the transaction.
    :rtype: Transaction
    """
    try:
        new_txn = create_transaction(db, current_user, transaction)
        logger.info(f"Added new transaction for user {current_user['id']}")
        return new_txn
    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        raise HTTPException(status_code=500, detail="Error adding transaction.")

@router.post("/update", summary="Update a transaction's category")
def update_txn(
    update_request: UpdateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update the category of an existing transaction for the current user.

    :param update_request (UpdateTransactionRequest): Update transaction data.
    :param db (Session): Database session dependency.
    :param current_user (dict): Current authenticated user dependency.
    :return dict: Updated transaction details.
    :raises HTTPException: If there is an error updating the transaction.
    :rtype: dict
    """
    try:
        updated = update_transaction_category(db, current_user, update_request)
        logger.info(f"Updated transaction for user {current_user['id']}")
        return updated
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail="Error updating transaction.")

@router.delete("/{transaction_id}", summary="Delete a transaction")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a transaction by its ID for the current user.

    :param transaction_id (int): ID of the transaction to delete.
    :param db (Session): Database session dependency.
    :param current_user (dict): Current authenticated user dependency.
    :return dict: Result of the delete operation.
    :raises HTTPException: If there is an error deleting the transaction.
    :rtype: dict
    """
    try:
        result = delete_transaction_by_id(db, current_user, transaction_id)
        logger.info(f"Deleted transaction {transaction_id} for user {current_user['id']}")
        return result
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(status_code=500, detail="Error deleting transaction.")