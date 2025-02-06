import io
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.models import Category

router = APIRouter()


@router.get("/", summary="Get all categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    categories_by_section = {}
    for cat in categories:
        categories_by_section.setdefault(cat.section, []).append(cat.category)
    return categories_by_section


@router.post("/update", summary="Update categories")
async def update_categories(file: UploadFile = Form(...), db: Session = Depends(get_db)):
    """
    Update categories from an uploaded Excel file.
    The file should contain columns named 'section' and 'category'.
    """
    logging.info("Updating categories...")
    try:
        df = pd.read_excel(io.BytesIO(file.file.read()))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    for _, row in df.iterrows():
        cat = Category(section=row['section'], category=row['category'])
        db.add(cat)
    db.commit()
    logging.info("Categories updated.")
    return {"message": "Categories updated."}


@router.post("/add-sections", summary="Add sections to transactions based on categories")
def add_sections(db: Session = Depends(get_db)):
    """
    Set the 'section' field on each transaction based on the category mapping.
    """
    from ..models import Transaction  # local import to avoid circular dependency
    logging.info("Adding sections to transactions...")
    transactions = db.query(Transaction).all()
    for txn in transactions:
        cat_entry = db.query(Category).filter(Category.category == txn.category).first()
        if cat_entry:
            txn.section = cat_entry.section
    db.commit()
    logging.info("Sections added to transactions.")
    return {"message": "Sections added to transactions."}
