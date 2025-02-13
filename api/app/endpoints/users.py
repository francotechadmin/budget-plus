from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..schemas.schemas import UserCreate, UserRead
from ..crud.crud import get_user, create_user
from ..database.database import get_db
from ..auth import get_current_user, get_user_info
import json

router = APIRouter()

@router.post("/", response_model=UserRead)
def create_user_endpoint(db: Session = Depends(get_db), current_user: dict = Depends(get_user_info)):
    print(json.dumps(current_user))
    user = UserCreate(
        id=current_user["sub"],
        email=current_user["email"],
        name=current_user["name"]
    )
    db_user = get_user(db, user_id=user.id)
    if db_user:
        return db_user
    return create_user(db=db, user=user)

@router.get("/", response_model=UserRead)
def read_user(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_user = get_user(db, user_id=current_user["sub"])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user