import datetime
from app.models.models import Transaction, Category, Section

# Helper function to insert a transaction directly into the DB.
def create_transaction(db, description, date, amount, category_name, user_id='auth0|1234567890'):
    # Look up the category by name.
    cat = db.query(Category).filter(Category.name == category_name, Category.user_id == user_id).first()
    if not cat:
        raise Exception(f"Category {category_name} not found.")
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

def test_get_totals(client, db_session, user_id='auth|1234567890'):
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
