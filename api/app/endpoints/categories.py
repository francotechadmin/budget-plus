import logging
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException
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
    