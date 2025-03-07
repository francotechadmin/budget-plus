import pytest
from app.models.models import Category, Section
from app.schemas.schemas import DescriptionRequest

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
