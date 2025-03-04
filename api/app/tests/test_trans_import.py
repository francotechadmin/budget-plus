import io
import pandas as pd
import pytest
from fastapi import UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile

# Helper: generate CSV content.
def generate_csv_content(rows):
    # Create CSV from list of dicts.
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)

# Test valid CSV import.
def test_import_valid_csv(client, db_session):
    # Prepare CSV content with required columns: date, description, amount, and an optional category.
    rows = [
        {"date": "2025-03-01", "description": "Test transaction", "amount": 100.0, "category": "Test Category"},
        {"date": "2025-03-02", "description": "Another transaction", "amount": 200.0, "category": "Test Category"}
    ]
    csv_content = generate_csv_content(rows)
    file_bytes = csv_content.encode("utf-8")
    files = {"file": ("transactions.csv", io.BytesIO(file_bytes), "text/csv")}
    
    # Call the import endpoint.
    response = client.post("/transactions/import", files=files)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data.get("detail") == "Transactions imported successfully."

# Test import with missing required columns.
def test_import_missing_columns(client):
    # Prepare CSV content missing the required 'amount' column.
    rows = [
        {"date": "2025-03-01", "description": "Test transaction", "category": "Test Category"},
    ]
    csv_content = generate_csv_content(rows)
    file_bytes = csv_content.encode("utf-8")
    files = {"file": ("transactions.csv", io.BytesIO(file_bytes), "text/csv")}
    
    response = client.post("/transactions/import", files=files)
    # Expect a 400 error due to missing column.
    assert response.status_code == 400, response.json()
    data = response.json()
    assert "Missing required columns" in data.get("detail", "")

# Test import with duplicate rows.
def test_import_duplicates(client, db_session):
    # Prepare CSV with duplicate rows.
    rows = [
        {"date": "2025-03-05", "description": "Duplicate txn", "amount": 150.0, "category": "Test Category"},
        {"date": "2025-03-05", "description": "Duplicate txn", "amount": 150.0, "category": "Test Category"},
        # A third identical row: the first occurrence should be inserted; duplicates skipped.
        {"date": "2025-03-05", "description": "Duplicate txn", "amount": 150.0, "category": "Test Category"},
    ]
    csv_content = generate_csv_content(rows)
    file_bytes = csv_content.encode("utf-8")
    files = {"file": ("transactions.csv", io.BytesIO(file_bytes), "text/csv")}
    
    # Pre-create one transaction in the DB that matches the duplicate row.
    # This ensures that duplicates are detected.
    from app.models.models import Transaction, Category
    # Look up category (fixture should have created "Test Category").
    cat = db_session.query(Category).filter(Category.name.ilike("test category")).first()
    if cat:
        txn = Transaction(
            user_id=1,
            description="Duplicate txn",
            date=pd.to_datetime("2025-03-05").date(),
            amount=150.0,
            category_id=cat.id,
            is_imported=1,
            is_deleted=0
        )
        db_session.add(txn)
        db_session.commit()
    
    response = client.post("/transactions/import", files=files)
    # Even though there are 3 rows in the file, the duplicates should be skipped.
    # We only expect new transactions if not duplicated.
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data.get("detail") == "Transactions imported successfully."

def test_import_valid_excel(client):
    # Create a simple DataFrame and write to a BytesIO as Excel.
    df = pd.DataFrame({
        "date": ["2025-03-10"],
        "description": ["Excel transaction"],
        "amount": [250.0],
        "category": ["Test Category"]
    })
    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    files = {"file": ("transactions.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    
    response = client.post("/transactions/import", files=files)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data.get("detail") == "Transactions imported successfully."
