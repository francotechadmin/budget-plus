# app/endpoints/transactions_import.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.transaction_service import import_transactions_service
from app.database.database import get_db
from app.auth import get_current_user

router = APIRouter()

@router.post("/import", summary="Upload bank transactions in bulk (standard format)")
async def import_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        return await import_transactions_service(file, db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error importing transactions.")
