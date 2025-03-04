from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.transaction_import_service import import_transactions_service
from app.database.database import get_db
from app.auth import get_current_user
from ..utils.logger import get_logger
from fastapi.exceptions import RequestValidationError as BadRequestException
from fastapi import HTTPException as FastAPIHTTPException  # for clarity

logger = get_logger(__name__)
router = APIRouter()

@router.post("/import", summary="Upload bank transactions in bulk (standard format)")
async def import_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a file containing bank transactions in a standard format (CSV or Excel).
    The file should contain columns for date, description, and amount.
    The endpoint will parse the file and import the transactions into the database.

    Args:
        file (UploadFile): The file containing bank transactions.
        db (Session): Database session dependency.
        current_user (dict): Current authenticated user dependency.

    Returns:
        dict: A message indicating the result of the import operation.

    Raises:
        HTTPException: If the file format is not supported or required columns are missing.
    """
    try:
        return await import_transactions_service(file, db, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error importing transactions.")
