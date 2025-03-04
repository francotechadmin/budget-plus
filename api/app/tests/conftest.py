import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.database import Base, get_db
from app.auth import get_current_user
from app.models.models import Category, Section

# Use a file-based SQLite database for testing.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Drop and create the database schema.
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Override the get_db dependency.
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Override get_current_user to simulate an authenticated user.
def override_get_current_user():
    return {"sub": 1}

app.dependency_overrides[get_current_user] = override_get_current_user

# Provide a client fixture.
@pytest.fixture(scope="session")
def client():
    test_client = TestClient(app)
    yield test_client
    # Teardown: remove the test database file after all tests in this module run.
    if os.path.exists("./test.db"):
        os.remove("./test.db")

# Fixture to pre-populate necessary test data.
@pytest.fixture(autouse=True)
def setup_db():
    db = TestingSessionLocal()
    # Clear tables to ensure a clean slate.
    db.query(Category).delete()
    db.query(Section).delete()
    db.commit()

    # Create a test section.
    test_section = Section(name="Test Section")
    db.add(test_section)
    db.commit()
    db.refresh(test_section)

    # Pre-populate categories.
    for cat_name in [
        "Test Category",
        "Old Category",
        "New Category",
        "Test Delete",
        "Uncategorized",
    ]:
        cat = Category(
            name=cat_name,
            description="Test category",
            section_id=test_section.id,
            user_id=1,
        )
        db.add(cat)
    db.commit()
    db.close()

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Clean up the test database file after tests run.
def teardown_module(module):
    if os.path.exists("./test.db"):
        os.remove("./test.db")
