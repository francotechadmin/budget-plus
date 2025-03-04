from ..utils.logger import get_logger
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..auth import get_current_user
from ..models.models import Category, Section
from ..schemas.schemas import DescriptionRequest
from ..transaction_categorization.model import predict_category_with_confidence

router = APIRouter()

# Configure logging
logger = get_logger(__name__)
@router.get("/", summary="Get all categories")
def get_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve all categories for the current user,
    grouped by section name (retrieved via a join with the Section table).

    :param db: The database session.
    :param user_id: The ID of the user to retrieve.
    :return: A dictionary where keys are section names and values are lists of category names.
    :raises HTTPException: If there is an error retrieving categories.
    :rtype: dict
    """
    logger.info(f"Fetching categories for user: {current_user['sub']}")
    
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
    
    logger.info(f"Categories fetched: {categories_by_section}")
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

    :param request (DescriptionRequest): The request containing the transaction description.
    :param db (Session): Database session dependency.
    :param current_user (dict): Current authenticated user dependency.
    :return JSONResponse: A response containing the predicted category, confidence, and uncertainty.
    """
    description = request.description
    if not description:
        logger.error("Description is required but not provided.")
        raise HTTPException(status_code=400, detail="Description is required.") 
    
    logger.info(f"Predicting category for description: {description}")
    
    # Use the pre-trained model to predict the category
    predicted_category, confidence, is_uncertain = predict_category_with_confidence(description)
    logger.info(f"Predicted category: {predicted_category}, Confidence: {confidence}, Uncertain: {is_uncertain}")
    
    return JSONResponse(
        content={
            "predicted_category": predicted_category,
            "confidence": confidence,
            "is_uncertain": str(is_uncertain)
        }
    )