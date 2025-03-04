# app/endpoints/transactions_crud.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.transaction_service import (
    get_all_transactions,
    create_transaction,
    update_transaction_category,
    delete_transaction_by_id,
)
from app.database.database import get_db
from app.auth import get_current_user
from app.schemas.schemas import NewTransactionRequest, UpdateTransactionRequest

router = APIRouter()

@router.get("/", summary="Get all transactions")
def get_transactions(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        transactions = get_all_transactions(db, current_user)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving transactions.")

@router.post("/", summary="Add a new transaction")
def add_transaction(
    transaction: NewTransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        new_txn = create_transaction(db, current_user, transaction)
        return new_txn
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error adding transaction.")

@router.post("/update", summary="Update a transaction's category")
def update_txn(
    update_request: UpdateTransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        updated = update_transaction_category(db, current_user, update_request)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating transaction.")

@router.delete("/{transaction_id}", summary="Delete a transaction")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        return delete_transaction_by_id(db, current_user, transaction_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting transaction.")
