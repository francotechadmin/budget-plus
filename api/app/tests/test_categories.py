import pytest
from app.models.models import Category, Section
from app.schemas.schemas import DescriptionRequest

def test_get_categories(client, db_session):
    # Clear any existing sections and categories.
    db_session.query(Category).delete()
    db_session.query(Section).delete()
    db_session.commit()

    # Create two sections.
    section_a = Section(name="Section A", user_id='auth0|1234567890')
    section_b = Section(name="Section B", user_id='auth0|1234567890')
    db_session.add_all([section_a, section_b])
    db_session.commit()
    db_session.refresh(section_a)
    db_session.refresh(section_b)

    # Create categories in each section.
    cat1 = Category(name="Category 1", description="Desc 1", section_id=section_a.id, user_id='auth0|1234567890')
    cat2 = Category(name="Category 2", description="Desc 2", section_id=section_a.id, user_id='auth0|1234567890')
    cat3 = Category(name="Category 3", description="Desc 3", section_id=section_b.id, user_id='auth0|1234567890')
    db_session.add_all([cat1, cat2, cat3])
    db_session.commit()

    response = client.get("/categories/")
    assert response.status_code == 200, response.json()
    data = response.json()
    # Expect keys to be the section names.
    assert "Section A" in data
    assert "Section B" in data
    # Check that the corresponding categories are returned.
    assert "Category 1" in data["Section A"]
    assert "Category 2" in data["Section A"]
    assert "Category 3" in data["Section B"]

def test_predict_category_endpoint(client, monkeypatch):
    # Override the prediction function in the categories endpoint.
    def fake_predict_category_with_confidence(description):
        return ("Fake Category", 0.95, False)
    
    monkeypatch.setattr(
        "app.endpoints.categories.predict_category_with_confidence",
        fake_predict_category_with_confidence
    )

    payload = {"description": "Test description"}
    response = client.post("/categories/predict", json=payload)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["predicted_category"] == "Fake Category"
    assert data["confidence"] == 0.95
    # Note: is_uncertain is returned as a string.
    assert data["is_uncertain"] == "False"

def test_predict_category_endpoint_no_description(client):
    # Test the endpoint returns 400 if description is empty.
    payload = {"description": ""}
    response = client.post("/categories/predict", json=payload)
    assert response.status_code == 400, response.json()
    data = response.json()
    assert "Description is required" in data["detail"]
