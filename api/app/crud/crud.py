from sqlalchemy.orm import Session
from ..models.models import User, Section, Category
from ..schemas.schemas import UserCreate
from ..utils.defaults import default_sections


def get_user(db: Session, user_id: int):
    """
    Get a user by ID.

    Args:
        db: The database session.
        user_id: The ID of the user to retrieve.
    """
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    """
    Create a new user and return the created user object.

    Args:
        db: The database session.
        user: The user data to create.
    """
    db_user = User(
        id=user.id,
        email=user.email,
        name=user.name,        
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    created_sections = create_default_sections(db, user.id, default_sections)
    create_default_categories(db, user.id, created_sections)
    return db_user

def create_default_sections(db: Session, user_id: str, default_sections: list) -> list:
    """
    Create default sections for a new user based on a list of default section objects.
    
    Returns a list of the created Section ORM objects.
    """
    created_sections = {}
    for default_sec in default_sections:
        section_name = default_sec["section"]
        section = Section(
            user_id=user_id,
            name=section_name,
            description="",  # Default description (can be adjusted)
        )
        db.add(section)
        created_sections[section_name] = default_sec
        created_sections[section_name]["db_section"] = section

    db.commit()  # Commit all sections at once

    # Refresh to load auto-generated fields (like id)
    for section in created_sections.values():
        db.refresh(section["db_section"])
        
    return created_sections

def create_default_categories(db: Session, user_id: str, created_sections: dict) -> list:
    """
    Create default categories for each section for a new user.
    
    Args:
        db: The database session.
        user_id: The user's ID.
        created_sections: A dictionary of created sections with their names and categories.
    
    Returns:
        A list of created Category ORM objects.
    """
    created_categories = [] 
    
    for created_sec in created_sections.values():
        section = created_sec["db_section"]
        categories = created_sec["categories"]
        for category_name in categories:
            category = Category(
                user_id=user_id,
                section_id=section.id,
                name=category_name,
                description="",  # Default description (can be adjusted)
            )
            db.add(category)
            created_categories.append(category)
    
    db.commit()  # Commit all categories at once

    # Refresh each category to get generated fields (like id)
    for category in created_categories:
        db.refresh(category)
    
    return created_categories
