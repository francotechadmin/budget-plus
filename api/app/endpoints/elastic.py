import io
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, Form, HTTPException, Depends
from ..schemas.schemas import DescriptionRequest
from ..elasticsearch_simple_client.uploader import Uploader
from ..elasticsearch_simple_client.searcher import Searcher
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models.models import Transaction

router = APIRouter()


@router.post("/add-data", summary="Add data to Elasticsearch")
async def add_data(file: UploadFile = Form(...)):
    """
    Upload data (an Excel file) to Elasticsearch.
    The file must contain the columns 'description' and 'annotated_category'.
    """
    logging.info("Adding data to Elasticsearch...")
    try:
        df = pd.read_excel(io.BytesIO(file.file.read()))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    es_uploader = Uploader()
    es_uploader.post_df(df[['description', 'annotated_category']])
    logging.info("Data added to Elasticsearch.")
    return {"message": "Data added to Elasticsearch."}


@router.post("/get-categories", summary="Get category for a description from Elasticsearch")
def get_categories(description_request: DescriptionRequest):
    description = description_request.description
    logging.info(f"Getting categories for description: {description}")
    searcher = Searcher()
    es_result = searcher.execute_search(
        field="description", 
        shoulds=[description]
    )["hits"]["hits"]
    category = es_result[0]["_source"]["annotated_category"] if es_result else "Unknown"
    logging.info(f"Category found: {category}")
    return {"category": category}


@router.post("/categorize-transactions", summary="Categorize transactions via Elasticsearch")
def categorize_transactions(db: Session = Depends(get_db)):
    """
    Update uncategorized transactions by querying Elasticsearch.
    """
    logging.info("Categorizing transactions...")
    searcher = Searcher()
    txns = db.query(Transaction).filter(Transaction.is_indexed == 0).all()
    for txn in txns:
        es_result = searcher.execute_search(
            field="description",
            shoulds=[txn.description]
        )["hits"]["hits"]
        txn.category = es_result[0]["_source"]["annotated_category"] if es_result else "Unknown"
    db.commit()
    logging.info("Transactions categorized.")
    return {"message": "Transactions categorized."}
