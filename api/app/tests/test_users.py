import pytest
from fastapi.testclient import TestClient
from app.models.models import User, Section, Category
from app.auth import get_user_info, get_current_user  # Ensure these are imported
from app.schemas.schemas import UserCreate, UserRead
from app.utils.defaults import default_sections


# Test creating a new user.
def test_create_user_new(client, db_session):
    user_id = "123"  # Use a string for the user id.
    # Ensure no user with this ID exists.
    db_session.query(User).filter(User.id == user_id).delete()
    db_session.commit()
    
    # Prepare a fake authenticated user info.
    fake_user_info = {"sub": user_id, "email": "newuser@example.com", "name": "New User"}
    
    # Override the get_user_info dependency.
    client.app.dependency_overrides[get_user_info] = lambda: fake_user_info

    response = client.post("/users/")
    # Expect 201 Created for a new user.
    assert response.status_code == 201, response.json()
    data = response.json()
    # Note: the created user now has string id.
    assert data["id"] == user_id
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    # Clean up the override.
    client.app.dependency_overrides.pop(get_user_info, None)

# Test creating an existing user.
def test_create_user_existing(client, db_session):
    user_id = "456"  # Use string id.
    # Pre-create a user.
    existing_user = User(id=user_id, email="existing@example.com", name="Existing User")
    db_session.add(existing_user)
    db_session.commit()
    
    fake_user_info = {"sub": user_id, "email": "existing@example.com", "name": "Existing User"}
    client.app.dependency_overrides[get_user_info] = lambda: fake_user_info

    response = client.post("/users/")
    # Expect 200 OK with a message indicating the user already exists.
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data.get("message") == "User already exists"
    client.app.dependency_overrides.pop(get_user_info, None)

# Test reading an existing user.
def test_read_user_found(client, db_session):
    user_id = "789"  # Use string id.
    # Pre-create the user.
    existing_user = User(id=user_id, email="readuser@example.com", name="Read User")
    db_session.add(existing_user)
    db_session.commit()
    
    fake_current_user = {"sub": user_id, "email": "readuser@example.com", "name": "Read User"}
    client.app.dependency_overrides[get_current_user] = lambda: fake_current_user

    response = client.get("/users/")
    assert response.status_code == 200, response.json()
    data = response.json()
    # Compare as strings.
    assert data["id"] == user_id
    assert data["email"] == "readuser@example.com"
    assert data["name"] == "Read User"
    client.app.dependency_overrides.pop(get_current_user, None)

# Test reading a user that does not exist.
def test_read_user_not_found(client, db_session):
    user_id = "999"  # Use string id.
    # Ensure no user exists with this id.
    db_session.query(User).filter(User.id == user_id).delete()
    db_session.commit()
    
    fake_current_user = {"sub": user_id, "email": "notfound@example.com", "name": "Not Found"}
    client.app.dependency_overrides[get_current_user] = lambda: fake_current_user

    response = client.get("/users/")
    # Expect a 404 error.
    assert response.status_code == 404, response.json()
    data = response.json()
    assert "User not found" in data["detail"]
    client.app.dependency_overrides.pop(get_current_user, None)

def test_create_user_creates_defaults(client, db_session):
    """
    Test that when a new user is created via the create_user_endpoint,
    the default sections and default categories are also created in the database.
    """
    # Use a fake user info with string id.
    user_id = "321"
    # Ensure no user, sections, or categories exist for this user.
    db_session.query(User).filter(User.id == user_id).delete()
    db_session.query(Section).filter(Section.user_id == user_id).delete()
    db_session.query(Category).filter(Category.user_id == user_id).delete()
    db_session.commit()

    fake_user_info = {"sub": user_id, "email": "default@example.com", "name": "Default User"}
    # Override get_user_info so that the endpoint creates a new user.
    client.app.dependency_overrides[get_user_info] = lambda: fake_user_info

    # Call the create user endpoint.
    response = client.post("/users/")
    assert response.status_code == 201, response.json()
    data = response.json()
    # Verify the user was created.
    assert data["id"] == user_id
    assert data["email"] == "default@example.com"
    assert data["name"] == "Default User"

    # Check that the default sections are created.
    sections = db_session.query(Section).filter(Section.user_id == user_id).all()
    # Number of sections should equal the number of defaults.
    assert len(sections) == len(default_sections), f"Expected {len(default_sections)} sections, got {len(sections)}"
    default_section_names = {sec["section"] for sec in default_sections}
    db_section_names = {sec.name for sec in sections}
    assert default_section_names.issubset(db_section_names), "Not all default sections were created."

    # For each default section, verify that its default categories were created.
    for default_sec in default_sections:
        section_name = default_sec["section"]
        expected_categories = set(default_sec.get("categories", []))
        # Get the section from the database.
        db_section = db_session.query(Section).filter(Section.user_id == user_id, Section.name == section_name).first()
        assert db_section is not None, f"Section {section_name} not found in DB."
        # Query categories for that section.
        db_categories = db_session.query(Category).filter(Category.user_id == user_id, Category.section_id == db_section.id).all()
        db_category_names = {cat.name for cat in db_categories}
        assert expected_categories.issubset(db_category_names), f"Missing categories in section {section_name}. Expected {expected_categories}, got {db_category_names}"

    # Clean up dependency override.
    client.app.dependency_overrides.pop(get_user_info, None)
