from app.models.models import Transaction
def test_get_transactions_empty(client, db_session):
    """Test that when there are no transactions, the endpoint returns an empty list."""
    # Clear any existing transactions.
    db_session.query(Transaction).delete()
    db_session.commit()

    response = client.get("/transactions/")
    # Uncomment below to debug error details.
    print(response.json())
    assert response.status_code == 200
    assert response.json() == []

def test_add_transaction(client):
    """Test that a new transaction can be added successfully."""
    payload = {
        "description": "Test transaction",
        "date": "2025-03-01",
        "amount": 100.0,
        "category": "Test Category",
    }
    response = client.post("/transactions/", json=payload)
    # print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Test transaction"
    assert data["amount"] == 100.0
    txn_id = data["id"]
    assert isinstance(txn_id, int)

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
    # print(update_response.json())
    assert update_response.status_code == 200
    updated_txn = update_response.json()
    assert updated_txn["id"] == txn_id
    assert updated_txn["category"] == "New Category"

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
    # print(delete_response.json())
    assert delete_response.status_code == 200

    # Verify the deleted transaction is not returned.
    get_response = client.get("/transactions/")
    assert get_response.status_code == 200
    txns = get_response.json()
    assert all(txn["id"] != txn_id for txn in txns)
