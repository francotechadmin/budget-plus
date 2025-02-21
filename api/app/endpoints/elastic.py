import io
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from ..schemas.schemas import DescriptionRequest
from ..elasticsearch_simple_client.uploader import Uploader
from ..elasticsearch_simple_client.searcher import Searcher
from ..database.database import get_db
from ..models.models import Transaction, Category, Section
from ..auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/add-data", summary="Add data to Elasticsearch")
async def add_data(file: UploadFile = Form(...)):
    """
    Upload data (an Excel file) to Elasticsearch.
    The file must contain the columns 'description' and 'annotated_category'.
    For default global rules, if the file does not contain a 'user_id' column,
    it will be set to "default" and a 'default' flag will be added with a value True.
    """
    logger.info("Adding data to Elasticsearch...")
    try:
        df = pd.read_excel(io.BytesIO(file.file.read()))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Ensure required fields exist.
    if 'user_id' not in df.columns:
        df['user_id'] = "default"
    if 'default' not in df.columns:
        df['default'] = True

    # Keep only the necessary columns.
    df = df[['description', 'annotated_category', 'user_id', 'default']]
    es_uploader = Uploader()
    es_uploader.post_df(df)
    logger.info("Data added to Elasticsearch.")
    return {"message": "Data added to Elasticsearch."}


@router.post("/get-categories", summary="Get category for a description from Elasticsearch")
def get_categories(description_request: DescriptionRequest):
    """
    Retrieve a suggested category for a given description from Elasticsearch.
    This endpoint uses fuzzy matching on the description and returns the 
    annotated_category from the top hit (or "Unknown" if none is found).
    """
    description = description_request.description
    logger.info(f"Getting category for description: {description}")
    searcher = Searcher()
    es_result = searcher.execute_search(
        field="description", 
        shoulds=[description]
    ).get("hits", {}).get("hits", [])
    
    # Log the full result for debugging if needed:
    logger.debug(f"Elasticsearch result: {es_result}") #2025-02-20 19:56:11 DEBUG:app.endpoints.elastic:Elasticsearch result: [{'_index': 'transactions', '_id': 'UUwqJpUBA6mwUY9GZgPq', '_score': 6.006294, '_source': {'user_id': 'default', 'description': 'BURGER JOINT', 'category': 'Fast Food', 'default': True}}]
    
    # Extract annotated_category or default to "Unknown"
    category = (
        es_result[0]["_source"].get("category") 
        if es_result and es_result[0]["_source"].get("category")
        else "Unknown"
    )
    logger.info(f"Category found: {category}")
    return {"category": category}



@router.post("/categorize-transactions", summary="Categorize transactions via Elasticsearch")
def categorize_transactions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update uncategorized transactions for the current user by querying Elasticsearch.
    For each transaction that has not been indexed (is_indexed==0), perform a fuzzy search
    on its description (using both user-specific data and global defaults) and update its category.
    Then mark the transaction as indexed.
    """
    logger.info(f"Categorizing transactions for user {current_user['sub']}...")
    searcher = Searcher()
    # Only process transactions that haven't been indexed and belong to the current user.
    txns = db.query(Transaction).filter(
        Transaction.is_indexed == 0,
        Transaction.user_id == current_user["sub"]
    ).all()
    for txn in txns:
        try:
            es_result = searcher.execute_search(
                field="description",
                shoulds=[txn.description],
                user_id=current_user["sub"]
            ).get("hits", {}).get("hits", [])
            new_category = es_result[0]["_source"].get("annotated_category") if es_result else "Unknown"
            logger.debug(f"Transaction {txn.id}: new category = {new_category}")
        except Exception as e:
            logger.error(f"Error searching for transaction {txn.id}: {e}")
            new_category = "Unknown"
        # Update transaction's category.
        txn.category = new_category
        txn.is_indexed = 1  # Mark as processed.
    try:
        db.commit()
        logger.info("Transactions categorized successfully.")
    except Exception as e:
        logger.error(f"Error committing transaction categorization: {e}")
        raise HTTPException(status_code=500, detail="Error categorizing transactions.")
    return {"message": "Transactions categorized."}
