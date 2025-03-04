# app/endpoints/transactions_reporting.py
from ..utils.logger import get_logger
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.transaction_resporting_service import (
    get_transactions_by_month_service,
    get_expense_totals_service,
    get_totals_service,
    get_grouped_transactions_service,
    get_history_service,
    get_transactions_range_service,
)
from app.database.database import get_db
from app.auth import get_current_user

# Configure logging
logger = get_logger(__name__)
router = APIRouter()

@router.get("/{year}/{month}", summary="Get transactions for a specific month")
def get_transactions_by_month(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch transactions for a specific month.

    This endpoint retrieves transactions for a given user for a specified year and month.

    Args:
        year (int): The year for which transactions are to be fetched.
        month (int): The month for which transactions are to be fetched.
        db (Session): Database session dependency.
        current_user (dict): The current authenticated user dependency.

    Returns:
        List[Transaction]: A list of transactions for the specified month.

    Raises:
        HTTPException: If there is an error retrieving transactions.
    """
    try:
        logger.info(f"Fetching transactions for user {current_user['id']} for {year}-{month}")
        return get_transactions_by_month_service(db, current_user, year, month)
    except Exception as e:
        logger.error(f"Error retrieving transactions by month: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transactions by month.")

@router.get("/expenses/{year}/{month}", summary="Get expense totals for a month")
def get_expense_totals(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate the total expenses for a given user for a specific year and month.
    Args:
        year (int): The year for which to calculate the expense totals.
        month (int): The month for which to calculate the expense totals.
        db (Session): The database session dependency.
        current_user (dict): The current authenticated user dependency.
    Returns:
        dict: A dictionary containing the total expenses for the specified year and month.
    Raises:
        HTTPException: If there is an error calculating the expense totals.
    """
    
    try:
        logger.info(f"Calculating expense totals for user {current_user['id']} for {year}-{month}")
        return get_expense_totals_service(db, current_user, year, month)
    except Exception as e:
        logger.error(f"Error calculating expense totals: {e}")
        raise HTTPException(status_code=500, detail="Error calculating expense totals.")

@router.get("/totals/{year}/{month}", summary="Get income and expenses totals for a month")
def get_totals(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate the total income and expenses for a given user for a specific year and month.
    Args:
        year (int): The year for which to calculate the totals.
        month (int): The month for which to calculate the totals.
        db (Session): The database session dependency.
        current_user (dict): The current authenticated user dependency.
    Returns:
        dict: A dictionary containing the total income and expenses for the specified year and month.
    Raises:
        HTTPException: If there is an error calculating the totals.
    """
    try:
        logger.info(f"Calculating totals for user {current_user['id']} for {year}-{month}")
        return get_totals_service(db, current_user, year, month)
    except Exception as e:
        logger.error(f"Error calculating totals: {e}")
        raise HTTPException(status_code=500, detail="Error calculating totals.")

@router.get("/grouped/{year}/{month}", summary="Get grouped transactions for a specific month")
def get_grouped_transactions(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch grouped transactions for a specific month.
    This endpoint retrieves transactions for a given user for a specified year and month,
    grouped by category.
    Args:
        year (int): The year for which transactions are to be fetched.
        month (int): The month for which transactions are to be fetched.
        db (Session): Database session dependency.
        current_user (dict): The current authenticated user dependency.
    Returns:
        dict: A dictionary containing the grouped transactions for the specified month.
    Raises:
        HTTPException: If there is an error retrieving grouped transactions.
    """
    try:
        logger.info(f"Fetching grouped transactions for user {current_user['id']} for {year}-{month}")
        return get_grouped_transactions_service(db, current_user, year, month)
    except Exception as e:
        logger.error(f"Error retrieving grouped transactions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving grouped transactions.")

@router.get("/history", summary="Get transaction history for the last six months")
def get_history(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Fetch transaction history for the last six months.
    This endpoint retrieves transactions for a given user for the last six months.
    Args:
        db (Session): Database session dependency.
        current_user (dict): The current authenticated user dependency.
    Returns:
        dict: A dictionary containing the transaction history for the last six months.
    Raises:
        HTTPException: If there is an error retrieving transaction history.
    """
    try:
        logger.info(f"Fetching transaction history for user {current_user['id']}")
        return get_history_service(db, current_user)
    except Exception as e:
        logger.error(f"Error retrieving transaction history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transaction history.")

@router.get("/range", summary="Get available transaction months")
def get_range(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Fetch the range of months for which transactions are available.
    This endpoint retrieves the start and end months for a given user.
    Args:
        db (Session): Database session dependency.
        current_user (dict): The current authenticated user dependency.
    Returns:
        dict: A dictionary containing the start and end months for transactions.
    Raises:
        HTTPException: If there is an error retrieving the transaction range.
    """
    try:
        logger.info(f"Fetching transaction range for user {current_user['id']}")
        return get_transactions_range_service(db, current_user)
    except Exception as e:
        logger.error(f"Error retrieving transaction range: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving transaction range.")
