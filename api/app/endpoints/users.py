from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..schemas.schemas import UserCreate, UserRead
from ..crud.crud import get_user, create_user
from ..database.database import get_db
from ..auth import get_current_user, get_user_info
import logging
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=UserRead)
def create_user_endpoint(db: Session = Depends(get_db), current_user: dict = Depends(get_user_info)):
    logger.info(f"Creating user with ID: {current_user['sub']}")
    user = UserCreate(
        id=current_user["sub"],
        email=current_user["email"],
        name=current_user["name"]
    )
    db_user = get_user(db, user_id=user.id)
    if db_user:
        logger.info(f"User with ID: {current_user['sub']} already exists.")
        return JSONResponse(status_code=200, content={"message": "User already exists"})
    logger.info(f"Creating new user with ID: {current_user['sub']}")
    return JSONResponse(status_code=201, content=create_user(db=db, user=user))

@router.get("/", response_model=UserRead)
def read_user(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    logger.info(f"Reading user with ID: {current_user['sub']}")
    db_user = get_user(db, user_id=current_user["sub"])
    if db_user is None:
        logger.error(f"User with ID: {current_user['sub']} not found.")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User with ID: {current_user['sub']} found.")
    return db_user