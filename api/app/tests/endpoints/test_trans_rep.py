import pytest
import datetime
from unittest.mock import patch
from app.models.models import Transaction, Category, Section

# Helper function to insert a transaction directly into the DB.
def create_transaction(db, description, date, amount, category_name, user_id='auth0|1234567890'):
    # Look up the category by name.
    cat = db.query(Category).filter(Category.name == category_name, Category.user_id == user_id).first()
    txn = Transaction(
        user_id=user_id,
        description=description,
        date=date,
        amount=amount,
        category_id=cat.id,
        is_deleted=0,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn

def test_get_transactions_by_month(client, db_session):
    # Clear any existing transactions.
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date1 = datetime.date(year, month, 10)
    date2 = datetime.date(year, month, 20)
    
    # Create two transactions in "Test Category". Our fixture sets "Test Category"
    # to belong to "Test Section".
    create_transaction(db_session, "Test txn 1", date1, 100.0, "Test Category")
    create_transaction(db_session, "Test txn 2", date2, 200.0, "Test Category")
    
    response = client.get(f"/transactions/{year}/{month}")
    assert response.status_code == 200
    data = response.json()
    # Expect a dictionary: {"Test Section": {"Test Category": [txns...]}}
    assert "Test Section" in data
    assert "Test Category" in data["Test Section"]
    txns = data["Test Section"]["Test Category"]
    # We expect exactly the two transactions we created.
    assert len(txns) == 2

def test_get_transactions_by_month_no_data(client, db_session):
    """Test retrieving transactions for a month with no data."""
    # Clear any existing transactions
    db_session.query(Transaction).delete()
    db_session.commit()
    
    # Request transactions for a month where we haven't created any
    year = 2024
    month = 1
    
    response = client.get(f"/transactions/{year}/{month}")
    assert response.status_code == 200
    data = response.json()
    # Response should be an empty dict as there are no transactions
    assert data == {}

def test_get_transactions_by_month_invalid_month(client):
    """Test retrieving transactions with an invalid month."""
    year = 2025
    month = 13  # Invalid month
    
    response = client.get(f"/transactions/{year}/{month}")
    assert response.status_code == 500
    assert "Error retrieving transactions by month" in response.json()["detail"]

def test_get_transactions_by_month_error(client):
    """Test error handling in get_transactions_by_month."""
    year = 2025
    month = 3
    
    with patch("app.endpoints.transactions_reporting.get_transactions_by_month_service") as mock_service:
        # Simulate a service error
        mock_service.side_effect = Exception("Database error")
        
        response = client.get(f"/transactions/{year}/{month}")
        assert response.status_code == 500
        assert "Error retrieving transactions by month" in response.json()["detail"]

def test_get_expense_totals(client, db_session):
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date_exp = datetime.date(year, month, 15)
    
    # Insert one expense transaction with amount 150.0.
    create_transaction(db_session, "Expense txn", date_exp, 150.0, "Test Category")
    
    response = client.get(f"/transactions/expenses/{year}/{month}")
    assert response.status_code == 200
    totals = response.json()
    # Expect "Test Category" to have a total of 150.0.
    assert "Test Category" in totals
    assert totals["Test Category"] == 150.0

def test_get_expense_totals_multiple_categories(client, db_session):
    """Test retrieving expense totals with multiple categories."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date = datetime.date(year, month, 15)
    
    # Ensure we have a second test category
    second_cat = db_session.query(Category).filter(Category.name == "Second Test").first()
    if not second_cat:
        section = db_session.query(Section).filter(Section.name == "Test Section").first()
        second_cat = Category(
            name="Second Test",
            description="Another test category",
            section_id=section.id,
            user_id='auth0|1234567890'
        )
        db_session.add(second_cat)
        db_session.commit()
    
    # Create transactions in two different categories
    create_transaction(db_session, "Expense 1", date, 100.0, "Test Category")
    create_transaction(db_session, "Expense 2", date, 200.0, "Second Test")
    
    response = client.get(f"/transactions/expenses/{year}/{month}")
    assert response.status_code == 200
    totals = response.json()
    
    # Check both categories have correct totals
    assert "Test Category" in totals
    assert "Second Test" in totals
    assert totals["Test Category"] == 100.0
    assert totals["Second Test"] == 200.0

def test_get_expense_totals_no_data(client, db_session):
    """Test retrieving expense totals for a month with no data."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2024
    month = 1
    
    response = client.get(f"/transactions/expenses/{year}/{month}")
    assert response.status_code == 200
    totals = response.json()
    # Response should be an empty dict
    assert totals == {}

def test_get_expense_totals_error(client):
    """Test error handling in get_expense_totals."""
    year = 2025
    month = 3
    
    with patch("app.endpoints.transactions_reporting.get_expense_totals_service") as mock_service:
        # Simulate a service error
        mock_service.side_effect = Exception("Database error")
        
        response = client.get(f"/transactions/expenses/{year}/{month}")
        assert response.status_code == 500
        assert "Error calculating expense totals" in response.json()["detail"]

def test_get_totals(client, db_session, user_id='auth0|1234567890'):
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date_exp = datetime.date(year, month, 12)
    date_inc = datetime.date(year, month, 5)
    
    # Insert an expense transaction.
    create_transaction(db_session, "Expense txn", date_exp, 100.0, "Test Category")
    
    # For income, we need a category under an 'Income' section.
    income_section = db_session.query(Section).filter(Section.name == "Income").first()
    if not income_section:
        income_section = Section(name="Income")
        db_session.add(income_section)
        db_session.commit()
        db_session.refresh(income_section)
    
    salary_cat = db_session.query(Category).filter(Category.name == "Salary", Category.user_id == user_id).first()
    if not salary_cat:
        salary_cat = Category(
            name="Salary",
            description="Income category",
            section_id=income_section.id,
            user_id='auth0|1234567890',
        )
        db_session.add(salary_cat)
        db_session.commit()
        db_session.refresh(salary_cat)
    
    # Insert an income transaction.
    create_transaction(db_session, "Income txn", date_inc, 300.0, "Salary")
    
    response = client.get(f"/transactions/totals/{year}/{month}")
    assert response.status_code == 200
    totals = response.json()
    # Expect income = 300.0 and expenses = 100.0.
    assert totals["income"] == 300.0
    assert totals["expenses"] == 100.0

def test_get_totals_no_income(client, db_session):
    """Test retrieving totals with expenses but no income."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date = datetime.date(year, month, 15)
    
    # Create only an expense transaction
    create_transaction(db_session, "Expense only", date, 150.0, "Test Category")
    
    response = client.get(f"/transactions/totals/{year}/{month}")
    assert response.status_code == 200
    totals = response.json()
    
    # Income should be 0, expenses should be 150.0
    assert totals["income"] == 0.0
    assert totals["expenses"] == 150.0

def test_get_totals_no_expenses(client, db_session, user_id='auth0|1234567890'):
    """Test retrieving totals with income but no expenses."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date = datetime.date(year, month, 15)
    
    # Ensure Income section and Salary category exist
    income_section = db_session.query(Section).filter(Section.name == "Income").first()
    if not income_section:
        income_section = Section(name="Income")
        db_session.add(income_section)
        db_session.commit()
        db_session.refresh(income_section)
    
    salary_cat = db_session.query(Category).filter(Category.name == "Salary", Category.user_id == user_id).first()
    if not salary_cat:
        salary_cat = Category(
            name="Salary",
            description="Income category",
            section_id=income_section.id,
            user_id='auth0|1234567890',
        )
        db_session.add(salary_cat)
        db_session.commit()
        db_session.refresh(salary_cat)
    
    # Create only an income transaction
    create_transaction(db_session, "Income only", date, 250.0, "Salary")
    
    response = client.get(f"/transactions/totals/{year}/{month}")
    assert response.status_code == 200
    totals = response.json()
    
    # Income should be 250.0, expenses should be 0
    assert totals["income"] == 250.0
    assert totals["expenses"] == 0.0

def test_get_totals_no_data(client, db_session):
    """Test retrieving totals for a month with no data."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2024
    month = 1
    
    response = client.get(f"/transactions/totals/{year}/{month}")
    assert response.status_code == 200
    totals = response.json()
    
    # Both income and expenses should be 0
    assert totals["income"] == 0.0
    assert totals["expenses"] == 0.0

def test_get_totals_error(client):
    """Test error handling in get_totals."""
    year = 2025
    month = 3
    
    with patch("app.endpoints.transactions_reporting.get_totals_service") as mock_service:
        # Simulate a service error
        mock_service.side_effect = Exception("Database error")
        
        response = client.get(f"/transactions/totals/{year}/{month}")
        assert response.status_code == 500
        assert "Error calculating totals" in response.json()["detail"]

def test_get_grouped_transactions(client, db_session):
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date1 = datetime.date(year, month, 8)
    date2 = datetime.date(year, month, 18)
    
    create_transaction(db_session, "Grouped txn 1", date1, 120.0, "Test Category")
    create_transaction(db_session, "Grouped txn 2", date2, 80.0, "Test Category")
    
    response = client.get(f"/transactions/grouped/{year}/{month}")
    assert response.status_code == 200
    data = response.json()
    # Expect a list of sections; look for "Test Section".
    grouped_section = next((item for item in data if item["section"] == "Test Section"), None)
    assert grouped_section is not None
    # In that section, look for "Test Category" with a computed total.
    cat_entry = next((cat for cat in grouped_section["categories"] if cat["name"] == "Test Category"), None)
    assert cat_entry is not None
    # Total should equal the sum of 120.0 and 80.0.
    assert cat_entry["total"] == 200.0

def test_get_grouped_transactions_multiple_sections(client, db_session, user_id='auth0|1234567890'):
    """Test retrieving grouped transactions with multiple sections."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2025
    month = 3
    date = datetime.date(year, month, 15)
    
    # Create a second section and category
    second_section = db_session.query(Section).filter(Section.name == "Second Section").first()
    if not second_section:
        second_section = Section(name="Second Section")
        db_session.add(second_section)
        db_session.commit()
        db_session.refresh(second_section)
    
    second_cat = db_session.query(Category).filter(Category.name == "Second Category", Category.user_id == user_id).first()
    if not second_cat:
        second_cat = Category(
            name="Second Category",
            description="Category in second section",
            section_id=second_section.id,
            user_id='auth0|1234567890',
        )
        db_session.add(second_cat)
        db_session.commit()
        db_session.refresh(second_cat)
    
    # Create transactions in both categories
    create_transaction(db_session, "Txn in first section", date, 100.0, "Test Category")
    create_transaction(db_session, "Txn in second section", date, 150.0, "Second Category")
    
    response = client.get(f"/transactions/grouped/{year}/{month}")
    assert response.status_code == 200
    data = response.json()
    
    # Check both sections are in the response
    first_section = next((item for item in data if item["section"] == "Test Section"), None)
    second_section = next((item for item in data if item["section"] == "Second Section"), None)
    
    assert first_section is not None
    assert second_section is not None
    
    # Check the category totals in each section
    first_cat = next((cat for cat in first_section["categories"] if cat["name"] == "Test Category"), None)
    second_cat = next((cat for cat in second_section["categories"] if cat["name"] == "Second Category"), None)
    
    assert first_cat is not None
    assert second_cat is not None
    assert first_cat["total"] == 100.0
    assert second_cat["total"] == 150.0

def test_get_grouped_transactions_no_data(client, db_session):
    """Test retrieving grouped transactions for a month with no data."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    year = 2024
    month = 1
    
    response = client.get(f"/transactions/grouped/{year}/{month}")
    assert response.status_code == 200
    data = response.json()
    
    # Response should be an empty list
    assert data == []

def test_get_grouped_transactions_error(client):
    """Test error handling in get_grouped_transactions."""
    year = 2025
    month = 3
    
    with patch("app.endpoints.transactions_reporting.get_grouped_transactions_service") as mock_service:
        # Simulate a service error
        mock_service.side_effect = Exception("Database error")
        
        response = client.get(f"/transactions/grouped/{year}/{month}")
        assert response.status_code == 500
        assert "Error retrieving grouped transactions" in response.json()["detail"]

def test_get_history(client, db_session):
    db_session.query(Transaction).delete()
    db_session.commit()
    
    # Insert transactions in February and March 2025.
    txn_feb = datetime.date(2025, 2, 15)
    txn_mar = datetime.date(2025, 3, 10)
    create_transaction(db_session, "Feb txn 1", txn_feb, 50.0, "Test Category")
    create_transaction(db_session, "Feb txn 2", txn_feb, 70.0, "Test Category")
    create_transaction(db_session, "Mar txn", txn_mar, 200.0, "Test Category")
    
    response = client.get("/transactions/history")
    assert response.status_code == 200
    history = response.json()
    # Expect keys like "February 2025" and "March 2025".
    feb_key = "February 2025"
    mar_key = "March 2025"
    assert feb_key in history
    assert mar_key in history
    # For February, expenses should sum to 120.0; for March, 200.0.
    assert history[feb_key]["expenses"] == 120.0
    assert history[mar_key]["expenses"] == 200.0

def test_get_history_with_income(client, db_session, user_id='auth0|1234567890'):
    """Test retrieving history with both income and expenses."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    # Ensure Income section and Salary category exist
    income_section = db_session.query(Section).filter(Section.name == "Income").first()
    if not income_section:
        income_section = Section(name="Income")
        db_session.add(income_section)
        db_session.commit()
        db_session.refresh(income_section)
    
    salary_cat = db_session.query(Category).filter(Category.name == "Salary", Category.user_id == user_id).first()
    if not salary_cat:
        salary_cat = Category(
            name="Salary",
            description="Income category",
            section_id=income_section.id,
            user_id='auth0|1234567890',
        )
        db_session.add(salary_cat)
        db_session.commit()
        db_session.refresh(salary_cat)
    
    # Create transactions over multiple months with both income and expenses
    date_jan = datetime.date(2025, 1, 15)
    date_feb = datetime.date(2025, 2, 15)
    
    # January - income and expense
    create_transaction(db_session, "Jan salary", date_jan, 1000.0, "Salary")
    create_transaction(db_session, "Jan expense", date_jan, 300.0, "Test Category")
    
    # February - income and expense
    create_transaction(db_session, "Feb salary", date_feb, 1000.0, "Salary")
    create_transaction(db_session, "Feb expense", date_feb, 400.0, "Test Category")
    
    response = client.get("/transactions/history")
    assert response.status_code == 200
    history = response.json()
    
    # Check both months have income and expenses
    jan_key = "January 2025"
    feb_key = "February 2025"
    
    assert jan_key in history
    assert feb_key in history
    
    assert history[jan_key]["income"] == 1000.0
    assert history[jan_key]["expenses"] == 300.0
    assert history[feb_key]["income"] == 1000.0
    assert history[feb_key]["expenses"] == 400.0

def test_get_history_no_data(client, db_session):
    """Test retrieving history when there are no transactions."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    response = client.get("/transactions/history")
    assert response.status_code == 200
    history = response.json()
    
    # Response should be an empty dict
    assert history == {}

def test_get_history_error(client):
    """Test error handling in get_history."""
    with patch("app.endpoints.transactions_reporting.get_history_service") as mock_service:
        # Simulate a service error
        mock_service.side_effect = Exception("Database error")
        
        response = client.get("/transactions/history")
        assert response.status_code == 500
        assert "Error retrieving transaction history" in response.json()["detail"]

def test_get_range(client, db_session):
    db_session.query(Transaction).delete()
    db_session.commit()
    
    # Insert transactions for January, February, and March 2025.
    dates = [
        datetime.date(2025, 1, 10),
        datetime.date(2025, 2, 20),
        datetime.date(2025, 3, 15),
    ]
    for i, d in enumerate(dates, start=1):
        create_transaction(db_session, f"Range txn {i}", d, 50.0 * i, "Test Category")
    
    response = client.get("/transactions/range")
    assert response.status_code == 200
    months = response.json()
    # Expect a list of months in descending order formatted as YYYY-MM.
    expected_months = ["2025-03", "2025-02", "2025-01"]
    assert months == expected_months

def test_get_range_wide_span(client, db_session):
    """Test retrieving transaction range with a wider time span."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    # Create transactions across multiple years
    dates = [
        datetime.date(2023, 12, 15),  # December 2023
        datetime.date(2024, 6, 20),   # June 2024
        datetime.date(2025, 1, 10),   # January 2025
    ]
    
    for i, d in enumerate(dates, start=1):
        create_transaction(db_session, f"Span txn {i}", d, 100.0, "Test Category")
    
    response = client.get("/transactions/range")
    assert response.status_code == 200
    months = response.json()
    
    # Expect months to be in descending order
    expected_months = ["2025-01", "2024-06", "2023-12"]
    assert months == expected_months

def test_get_range_single_month(client, db_session):
    """Test retrieving transaction range with only one month of data."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    # Create transactions for only one month
    date = datetime.date(2025, 3, 15)
    create_transaction(db_session, "Single month txn", date, 100.0, "Test Category")
    
    response = client.get("/transactions/range")
    assert response.status_code == 200
    months = response.json()
    
    # Expect just one month
    assert months == ["2025-03"]

def test_get_range_no_data(client, db_session):
    """Test retrieving transaction range when there are no transactions."""
    db_session.query(Transaction).delete()
    db_session.commit()
    
    response = client.get("/transactions/range")
    assert response.status_code == 200
    months = response.json()
    
    # Response should be an empty list
    assert months == []

def test_get_range_error(client):
    """Test error handling in get_range."""
    with patch("app.endpoints.transactions_reporting.get_transactions_range_service") as mock_service:
        # Simulate a service error
        mock_service.side_effect = Exception("Database error")
        
        response = client.get("/transactions/range")
        assert response.status_code == 500
        assert "Error retrieving transaction range" in response.json()["detail"]