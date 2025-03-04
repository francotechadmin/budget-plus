from ..utils.logger import get_logger
from sqlalchemy.orm import Session
from ..models.models import User, Section, Category
from ..schemas.schemas import UserCreate
from ..utils.defaults import default_sections

# Configure logging
logger = get_logger(__name__)

def get_user(db: Session, user_id: int):
    """
    Get a user by ID.

    :param db: The database session.
    :param user_id: The ID of the user to retrieve.
    :return: The user object if found, otherwise None.
    """
    logger.info(f"Fetching user with ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        logger.info(f"User found: {user}")
    else:
        logger.warning(f"No user found with ID: {user_id}")
    return user

def create_user(db: Session, user: UserCreate):
    """
    Create a new user and return the created user object.

    :param db: The database session.
    :param user: The user object to create.
    """
    logger.info(f"Creating user with email: {user.email}")
    db_user = User(
        id=user.id,
        email=user.email,
        name=user.name,        
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created with ID: {db_user.id}")

    created_sections = create_default_sections(db, user.id, default_sections)
    create_default_categories(db, user.id, created_sections)
    
    user = {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "is_admin": db_user.is_admin,
    }
    logger.info(f"User creation complete: {user}")
    return user

def create_default_sections(db: Session, user_id: str, default_sections: list) -> list:
    """
    Create default sections for a new user based on a list of default section objects.
    
    :param db: The database session.
    :param user_id: The ID of the user for whom to create sections.
    :param default_sections: A list of dictionaries representing default sections.
    :return: A list of created Section ORM objects.
    """
    logger.info(f"Creating default sections for user ID: {user_id}")
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
        logger.info(f"Section created: {section['db_section']}")

    return created_sections

def create_default_categories(db: Session, user_id: str, created_sections: dict) -> list:
    """
    Create default categories for each section for a new user.
    
    :param db: The database session.    
    :param user_id: The ID of the user for whom to create categories.
    :param created_sections: A dictionary of created sections.
    :return: A list of created Category ORM objects.
    """
    logger.info(f"Creating default categories for user ID: {user_id}")
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
        logger.info(f"Category created: {category}")
    
    return created_categories
