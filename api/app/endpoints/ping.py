from fastapi import APIRouter
from ..utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
router = APIRouter()

@router.get("/ping", summary="Health check endpoint")
async def pong():
    """
    Health check endpoint to verify the API is running.

    Returns:
        dict: A simple response indicating the API is alive.
    """
    logger.info("Ping endpoint hit")
    return {"ping": "pong!"}
