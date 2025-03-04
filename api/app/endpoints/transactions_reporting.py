# app/endpoints/transactions_reporting.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.transaction_service import (
    get_transactions_by_month_service,
    get_expense_totals_service,
    get_totals_service,
    get_grouped_transactions_service,
    get_history_service,
    get_transactions_range_service,
)
from app.database.database import get_db
from app.auth import get_current_user

router = APIRouter()

@router.get("/{year}/{month}", summary="Get transactions for a specific month")
def get_transactions_by_month(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        return get_transactions_by_month_service(db, current_user, year, month)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving transactions by month.")

@router.get("/expenses/{year}/{month}", summary="Get expense totals for a month")
def get_expense_totals(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        return get_expense_totals_service(db, current_user, year, month)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error calculating expense totals.")

@router.get("/totals/{year}/{month}", summary="Get income and expenses totals for a month")
def get_totals(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        return get_totals_service(db, current_user, year, month)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error calculating totals.")

@router.get("/grouped/{year}/{month}", summary="Get grouped transactions for a specific month")
def get_grouped_transactions(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        return get_grouped_transactions_service(db, current_user, year, month)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving grouped transactions.")

@router.get("/history", summary="Get transaction history for the last six months")
def get_history(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        return get_history_service(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving transaction history.")

@router.get("/range", summary="Get available transaction months")
def get_range(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        return get_transactions_range_service(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving transaction range.")
