import pytest
from unittest.mock import patch
from datetime import datetime, date
from app.models.models import Transaction, Category

def test_get_transactions_empty(client, db_session):
    """Test that when there are no transactions, the endpoint returns an empty list."""
    # Clear any existing transactions.
    db_session.query(Transaction).delete()
    db_session.commit()

    response = client.get("/transactions/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_transactions_multiple(client, db_session):
    """Test retrieving multiple transactions."""
    # Clear existing transactions
    db_session.query(Transaction).delete()
    db_session.commit()
    
    # First make sure the categories exist in the database
    # Add categories if they don't exist
    categories = ["Category A", "Category B"]
    for cat_name in categories:
        # Check if category exists
        cat = db_session.query(Category).filter(Category.name == cat_name).first()
        if not cat:
            # Create the category - assuming section_id and user_id are properly set in your fixtures
            section = db_session.query(Category).first().section_id  # Get a valid section ID
            user_id = "auth0|1234567890"  # From your conftest
            new_cat = Category(
                name=cat_name,
                description=f"Test {cat_name}",
                section_id=section,
                user_id=user_id
            )
            db_session.add(new_cat)
    db_session.commit()
    
    # Add multiple test transactions
    txns = [
        {
            "description": "Transaction 1",
            "date": "2025-03-01",
            "amount": 100.0,
            "category": "Category A",
        },
        {
            "description": "Transaction 2",
            "date": "2025-03-02",
            "amount": 200.0,
            "category": "Category B",
        },
        {
            "description": "Transaction 3",
            "date": "2025-03-03",
            "amount": 300.0,
            "category": "Category A",
        }
    ]
    
    # Create the transactions
    for txn in txns:
        response = client.post("/transactions/", json=txn)
        assert response.status_code == 200, f"Failed to create transaction: {response.json()}"
    
    # Get all transactions
    response = client.get("/transactions/")
    assert response.status_code == 200
    data = response.json()
    
    # Verify we have at least our 3 transactions
    # (There might be other transactions from other tests)
    assert len(data) >= 3
    
    # Find our test transactions in the response
    test_txns = [t for t in data if t["description"] in ["Transaction 1", "Transaction 2", "Transaction 3"]]
    
    # Verify our test transactions
    assert len(test_txns) == 3
    assert sum(t["amount"] for t in test_txns) == 600.0
    assert len([t for t in test_txns if t["category"] == "Category A"]) == 2
    assert len([t for t in test_txns if t["category"] == "Category B"]) == 1

def test_get_transactions_error(client):
    """Test error handling when retrieving transactions fails."""
    with patch("app.endpoints.transactions_crud.get_all_transactions") as mock_get:
        # Simulate an internal error
        mock_get.side_effect = Exception("Database error")
        
        response = client.get("/transactions/")
        assert response.status_code == 500
        assert "Error retrieving transactions" in response.json()["detail"]

def test_add_transaction(client):
    """Test that a new transaction can be added successfully."""
    payload = {
        "description": "Test transaction",
        "date": "2025-03-01",
        "amount": 100.0,
        "category": "Test Category",
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Test transaction"
    assert data["amount"] == 100.0
    txn_id = data["id"]
    assert isinstance(txn_id, int)

def test_add_transaction_with_decimal_amount(client):
    """Test adding a transaction with a decimal amount."""
    payload = {
        "description": "Decimal amount",
        "date": "2025-03-01",
        "amount": 99.99,
        "category": "Test Category",
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 99.99

def test_add_transaction_with_negative_amount(client):
    """Test adding a transaction with a negative amount."""
    payload = {
        "description": "Negative amount",
        "date": "2025-03-01",
        "amount": -50.0,
        "category": "Test Category",
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == -50.0

def test_add_transaction_error(client):
    """Test error handling when adding a transaction fails."""
    with patch("app.endpoints.transactions_crud.create_transaction") as mock_create:
        # Simulate an internal error
        mock_create.side_effect = Exception("Database error")
        
        payload = {
            "description": "Error transaction",
            "date": "2025-03-01",
            "amount": 100.0,
            "category": "Test Category",
        }
        response = client.post("/transactions/", json=payload)
        assert response.status_code == 500
        assert "Error adding transaction" in response.json()["detail"]

def test_add_transaction_invalid_date_format(client):
    """Test validation when date format is invalid."""
    payload = {
        "description": "Invalid date",
        "date": "03-01-2025",  # Wrong format, should be YYYY-MM-DD
        "amount": 100.0,
        "category": "Test Category",
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 422  # Validation error

def test_add_transaction_missing_required_field(client):
    """Test validation when a required field is missing."""
    # Missing description
    payload = {
        "date": "2025-03-01",
        "amount": 100.0,
        "category": "Test Category",
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 422  # Validation error

def test_update_transaction(client):
    """Test updating the category of an existing transaction."""
    # Create a new transaction.
    create_payload = {
        "description": "Transaction to update",
        "date": "2025-03-02",
        "amount": 50.0,
        "category": "Old Category",
    }
    create_response = client.post("/transactions/", json=create_payload)
    assert create_response.status_code == 200
    created_txn = create_response.json()
    txn_id = created_txn["id"]

    # Now update the transaction's category.
    update_payload = {
        "transaction_id": txn_id,
        "category": "New Category",
    }
    update_response = client.post("/transactions/update", json=update_payload)
    assert update_response.status_code == 200
    updated_txn = update_response.json()
    assert updated_txn["id"] == txn_id
    assert updated_txn["category"] == "New Category"

def test_update_nonexistent_transaction(client):
    """Test updating a transaction that doesn't exist."""
    # Use a transaction ID that doesn't exist
    update_payload = {
        "transaction_id": 999999,
        "category": "New Category",
    }
    with patch("app.endpoints.transactions_crud.update_transaction_category") as mock_update:
        # Simulate a "not found" error
        mock_update.side_effect = Exception("Transaction not found")
        
        response = client.post("/transactions/update", json=update_payload)
        assert response.status_code == 500
        assert "Error updating transaction" in response.json()["detail"]

def test_update_transaction_error(client):
    """Test error handling when updating a transaction fails."""
    # Create a transaction first
    create_payload = {
        "description": "Transaction for error test",
        "date": "2025-03-02",
        "amount": 50.0,
        "category": "Old Category",
    }
    create_response = client.post("/transactions/", json=create_payload)
    txn_id = create_response.json()["id"]
    
    with patch("app.endpoints.transactions_crud.update_transaction_category") as mock_update:
        # Simulate an internal error
        mock_update.side_effect = Exception("Database error")
        
        update_payload = {
            "transaction_id": txn_id,
            "category": "New Category",
        }
        response = client.post("/transactions/update", json=update_payload)
        assert response.status_code == 500
        assert "Error updating transaction" in response.json()["detail"]

def test_delete_transaction(client):
    """Test deleting a transaction and verifying it no longer appears."""
    # Create a new transaction to delete.
    create_payload = {
        "description": "Transaction to delete",
        "date": "2025-03-03",
        "amount": 75.0,
        "category": "Test Delete",
    }
    create_response = client.post("/transactions/", json=create_payload)
    assert create_response.status_code == 200
    created_txn = create_response.json()
    txn_id = created_txn["id"]

    # Delete the transaction.
    delete_response = client.delete(f"/transactions/{txn_id}")
    assert delete_response.status_code == 200

    # Verify the deleted transaction is not returned.
    get_response = client.get("/transactions/")
    assert get_response.status_code == 200
    txns = get_response.json()
    assert all(txn["id"] != txn_id for txn in txns)

def test_delete_nonexistent_transaction(client):
    """Test deleting a transaction that doesn't exist."""
    # Use a transaction ID that doesn't exist
    with patch("app.endpoints.transactions_crud.delete_transaction_by_id") as mock_delete:
        # Simulate a "not found" error
        mock_delete.side_effect = Exception("Transaction not found")
        
        response = client.delete("/transactions/999999")
        assert response.status_code == 500
        assert "Error deleting transaction" in response.json()["detail"]

def test_delete_transaction_error(client):
    """Test error handling when deleting a transaction fails."""
    # Create a transaction first
    create_payload = {
        "description": "Transaction for delete error test",
        "date": "2025-03-03",
        "amount": 75.0,
        "category": "Test Delete",
    }
    create_response = client.post("/transactions/", json=create_payload)
    txn_id = create_response.json()["id"]
    
    with patch("app.endpoints.transactions_crud.delete_transaction_by_id") as mock_delete:
        # Simulate an internal error
        mock_delete.side_effect = Exception("Database error")
        
        response = client.delete(f"/transactions/{txn_id}")
        assert response.status_code == 500
        assert "Error deleting transaction" in response.json()["detail"]

def test_multiple_operations_sequence(client, db_session):
    """Test a sequence of CRUD operations to ensure consistency."""
    # Start with a clean state for this test
    db_session.query(Transaction).filter(
        Transaction.description.in_(["Sequence transaction 1", "Sequence transaction 2"])
    ).delete(synchronize_session=False)
    db_session.commit()
    
    # Make sure the categories exist
    categories = ["Category X", "Category Y", "Updated Category"]
    for cat_name in categories:
        # Check if category exists
        cat = db_session.query(Category).filter(Category.name == cat_name).first()
        if not cat:
            # Create the category
            section = db_session.query(Category).first().section_id  # Get a valid section ID
            user_id = "auth0|1234567890"  # From your conftest
            new_cat = Category(
                name=cat_name,
                description=f"Test {cat_name}",
                section_id=section,
                user_id=user_id
            )
            db_session.add(new_cat)
    db_session.commit()
    
    # 1. Get initial transactions - may not be empty if other tests added transactions
    initial_response = client.get("/transactions/")
    assert initial_response.status_code == 200
    initial_count = len(initial_response.json())
    
    # 2. Add transactions
    txns = [
        {
            "description": "Sequence transaction 1",
            "date": "2025-03-01",
            "amount": 100.0,
            "category": "Category X",
        },
        {
            "description": "Sequence transaction 2",
            "date": "2025-03-02",
            "amount": 200.0,
            "category": "Category Y",
        }
    ]
    
    created_ids = []
    for txn in txns:
        response = client.post("/transactions/", json=txn)
        assert response.status_code == 200, f"Failed to create transaction: {response.json()}"
        created_ids.append(response.json()["id"])
    
    # 3. Verify transactions were added
    response = client.get("/transactions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == initial_count + 2, "Expected two new transactions to be added"
    
    # Find our test transactions
    sequence_txns = [t for t in data if t["description"] in ["Sequence transaction 1", "Sequence transaction 2"]]
    assert len(sequence_txns) == 2, "Expected to find both sequence transactions"
    
    # 4. Update a transaction
    txn_to_update = next(t for t in sequence_txns if t["description"] == "Sequence transaction 1")
    update_payload = {
        "transaction_id": txn_to_update["id"],
        "category": "Updated Category",
    }
    response = client.post("/transactions/update", json=update_payload)
    assert response.status_code == 200, f"Failed to update transaction: {response.json()}"
    
    # 5. Verify update worked
    response = client.get("/transactions/")
    assert response.status_code == 200
    data = response.json()
    updated_txn = next(t for t in data if t["id"] == txn_to_update["id"])
    assert updated_txn["category"] == "Updated Category", "Category was not updated correctly"
    
    # 6. Delete a transaction
    txn_to_delete = next(t for t in sequence_txns if t["description"] == "Sequence transaction 2")
    response = client.delete(f"/transactions/{txn_to_delete['id']}")
    assert response.status_code == 200, f"Failed to delete transaction: {response.json()}"
    
    # 7. Verify final state
    response = client.get("/transactions/")
    assert response.status_code == 200
    data = response.json()
    
    # The first transaction should still exist with updated category
    first_txn = next((t for t in data if t["id"] == txn_to_update["id"]), None)
    assert first_txn is not None, "First transaction should still exist"
    assert first_txn["description"] == "Sequence transaction 1"
    assert first_txn["category"] == "Updated Category"
    
    # The second transaction should be gone
    second_txn = next((t for t in data if t["id"] == txn_to_delete["id"]), None)
    assert second_txn is None, "Second transaction should have been deleted"