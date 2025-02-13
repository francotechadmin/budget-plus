from sqlalchemy.orm import Session
from ..models.models import User
from ..schemas.schemas import UserCreate


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(
        id=user.id,
        email=user.email,
        name=user.name,        
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user