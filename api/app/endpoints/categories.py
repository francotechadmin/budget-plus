import io
import logging
from fastapi.responses import JSONResponse
import pandas as pd
from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..auth import get_current_user
from ..models.models import Category, Section
from ..schemas.schemas import DescriptionRequest
from ..transaction_categorization.model import predict_category_with_confidence

router = APIRouter()


@router.get("/", summary="Get all categories")
def get_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve all categories for the current user,
    grouped by section name (retrieved via a join with the Section table).
    """
    # Join Category with Section and filter by the current user
    results = (
        db.query(Category, Section.name.label("section_name"))
        .join(Section, Category.section_id == Section.id)
        .filter(Category.user_id == current_user["sub"])
        .all()
    )
    
    categories_by_section = {}
    for category, section_name in results:
        categories_by_section.setdefault(section_name, []).append(category.name)
    return categories_by_section


@router.post("/update", summary="Update categories")
async def update_categories(
    file: UploadFile = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update categories from an uploaded Excel file.
    The Excel file should contain columns named 'section' and 'category'.
    For each row, the endpoint will look up (or optionally create) the section
    for the current user and then add (or update) the category.
    """
    logging.info("Updating categories...")
    try:
        df = pd.read_excel(io.BytesIO(file.file.read()))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    for _, row in df.iterrows():
        section_name = row["section"]
        category_name = row["category"]
        
        # Lookup the section for this user by name
        section_obj = (
            db.query(Section)
            .filter(Section.name == section_name, Section.user_id == current_user["sub"])
            .first()
        )
        if not section_obj:
            # Optionally create the section if it doesn't exist
            section_obj = Section(
                user_id=current_user["sub"],
                name=section_name,
                description=""
            )
            db.add(section_obj)
            db.commit()
            db.refresh(section_obj)
        
        # Lookup the category in this section for the current user
        category_obj = (
            db.query(Category)
            .filter(
                Category.name == category_name,
                Category.section_id == section_obj.id,
                Category.user_id == current_user["sub"]
            )
            .first()
        )
        if not category_obj:
            # Create new category if it doesn't exist
            category_obj = Category(
                user_id=current_user["sub"],
                section_id=section_obj.id,
                name=category_name,
                description=""
            )
            db.add(category_obj)
        # Else, you might update existing category details if needed.
    
    db.commit()
    logging.info("Categories updated.")
    return {"message": "Categories updated."}


@router.post("/add-sections", summary="Add sections to transactions based on categories")
def add_sections(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update each transaction for the current user by setting its 'section' field
    based on the section of the associated category.
    Assumes that Transaction stores a foreign key to Category (category_id)
    and has a separate cached 'section' field that we want to update.
    """
    from ..models.models import Transaction  # local import to avoid circular dependency

    logging.info("Adding sections to transactions...")
    
    # Query transactions only for the current user
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user["sub"]).all()
    for txn in transactions:
        # Lookup the Category for this transaction (using the foreign key)
        category_obj = db.query(Category).filter(Category.id == txn.category_id).first()
        if category_obj:
            # Retrieve the Section record for this category
            section_obj = db.query(Section).filter(Section.id == category_obj.section_id).first()
            if section_obj:
                txn.section = section_obj.name
    db.commit()
    logging.info("Sections added to transactions.")
    return {"message": "Sections added to transactions."}
 
@router.post("/predict", summary="Predict category for a transaction")
def predict_category_endpoint(
    request: DescriptionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Predict the category for a given transaction description.
    The prediction is based on a pre-trained model.
    """
    description = request.description
    if not description:
        raise HTTPException(status_code=400, detail="Description is required.") 
    logging.info(f"Predicting category for description: {description}")
    
    # Use the pre-trained model to predict the category
    predicted_category, confidence, is_uncertain = predict_category_with_confidence(description)
    logging.info(f"Predicted category: {predicted_category}, Confidence: {confidence}, Uncertain: {is_uncertain}")
    
    return JSONResponse(
        content={
            "predicted_category": predicted_category,
            "confidence": confidence,
            "is_uncertain": str(is_uncertain)
        }
    )
    