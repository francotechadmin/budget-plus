import pytest
import datetime
import calendar
import pandas as pd
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.models.models import Transaction, Category, Section
from app.services.transaction_reporting_service import (
    get_transactions_by_month_service,
    get_expense_totals_service,
    get_totals_service,
    get_grouped_transactions_service,
    get_history_service,
    get_transactions_range_service
)

# Mock user for testing
MOCK_USER = {"sub": "auth0|1234567890", "email": "test@example.com"}

class TestTransactionReportingService:
    
    @pytest.fixture
    def setup_test_data(self, db_session):
        """Set up test data for reporting services tests."""
        # Clear existing data
        db_session.query(Transaction).delete()
        db_session.commit()
        
        # Create sections
        income_section = db_session.query(Section).filter(Section.name == "Income").first()
        if not income_section:
            income_section = Section(name="Income")
            db_session.add(income_section)
            db_session.commit()
            db_session.refresh(income_section)
        
        expenses_section = db_session.query(Section).filter(Section.name == "Expenses").first()
        if not expenses_section:
            expenses_section = Section(name="Expenses")
            db_session.add(expenses_section)
            db_session.commit()
            db_session.refresh(expenses_section)
        
        # Create categories
        categories = {
            "Income": ["Salary", "Freelance"],
            "Expenses": ["Groceries", "Dining", "Housing", "Transportation"]
        }
        
        created_categories = {}
        
        for section_name, category_names in categories.items():
            section = income_section if section_name == "Income" else expenses_section
            for cat_name in category_names:
                cat = db_session.query(Category).filter(
                    Category.name == cat_name,
                    Category.user_id == MOCK_USER["sub"]
                ).first()
                
                if not cat:
                    cat = Category(
                        name=cat_name,
                        description=f"{cat_name} category",
                        section_id=section.id,
                        user_id=MOCK_USER["sub"]
                    )
                    db_session.add(cat)
                    db_session.commit()
                    db_session.refresh(cat)
                
                created_categories[cat_name] = cat
        
        # Create transactions across multiple months
        transactions = [
            # March 2025 - Income
            {"description": "March Salary", "date": datetime.date(2025, 3, 15), "amount": 5000.0, "category": "Salary"},
            {"description": "March Freelance", "date": datetime.date(2025, 3, 20), "amount": 1000.0, "category": "Freelance"},
            
            # March 2025 - Expenses
            {"description": "March Rent", "date": datetime.date(2025, 3, 1), "amount": 1500.0, "category": "Housing"},
            {"description": "March Groceries 1", "date": datetime.date(2025, 3, 5), "amount": 200.0, "category": "Groceries"},
            {"description": "March Groceries 2", "date": datetime.date(2025, 3, 15), "amount": 150.0, "category": "Groceries"},
            {"description": "March Restaurant 1", "date": datetime.date(2025, 3, 10), "amount": 75.0, "category": "Dining"},
            {"description": "March Restaurant 2", "date": datetime.date(2025, 3, 20), "amount": 85.0, "category": "Dining"},
            {"description": "March Gas", "date": datetime.date(2025, 3, 25), "amount": 50.0, "category": "Transportation"},
            
            # April 2025 - Income
            {"description": "April Salary", "date": datetime.date(2025, 4, 15), "amount": 5000.0, "category": "Salary"},
            
            # April 2025 - Expenses
            {"description": "April Rent", "date": datetime.date(2025, 4, 1), "amount": 1500.0, "category": "Housing"},
            {"description": "April Groceries", "date": datetime.date(2025, 4, 10), "amount": 180.0, "category": "Groceries"},
            {"description": "April Restaurant", "date": datetime.date(2025, 4, 20), "amount": 65.0, "category": "Dining"},
            
            # May 2025 - Partial data
            {"description": "May Salary", "date": datetime.date(2025, 5, 15), "amount": 5000.0, "category": "Salary"},
            {"description": "May Rent", "date": datetime.date(2025, 5, 1), "amount": 1500.0, "category": "Housing"},
        ]
        
        for txn_data in transactions:
            cat = created_categories[txn_data["category"]]
            txn = Transaction(
                user_id=MOCK_USER["sub"],
                description=txn_data["description"],
                date=txn_data["date"],
                amount=txn_data["amount"],
                category_id=cat.id,
                is_deleted=0
            )
            db_session.add(txn)
        
        db_session.commit()
        
        # Return the created objects for reference in tests
        return {
            "sections": {"Income": income_section, "Expenses": expenses_section},
            "categories": created_categories,
        }

    def test_get_transactions_by_month_service(self, db_session, setup_test_data):
        """Test retrieving transactions for a specific month."""
        # Test for March 2025
        year, month = 2025, 3
        
        result = get_transactions_by_month_service(db_session, MOCK_USER, year, month)
        
        # Verify structure
        assert "Income" in result
        assert "Expenses" in result
        
        # Verify income transactions
        assert "Salary" in result["Income"]
        assert "Freelance" in result["Income"]
        assert len(result["Income"]["Salary"]) == 1
        assert len(result["Income"]["Freelance"]) == 1
        
        # Verify expense transactions
        assert "Housing" in result["Expenses"]
        assert "Groceries" in result["Expenses"]
        assert "Dining" in result["Expenses"]
        assert "Transportation" in result["Expenses"]
        
        # Check specific counts
        assert len(result["Expenses"]["Groceries"]) == 2
        assert len(result["Expenses"]["Dining"]) == 2
        assert len(result["Expenses"]["Housing"]) == 1
        assert len(result["Expenses"]["Transportation"]) == 1
        
        # Verify transaction details
        salary = result["Income"]["Salary"][0]
        assert salary["amount"] == 5000.0
        assert salary["description"] == "March Salary"
        
        # Check for specific transactions
        groceries = [t["description"] for t in result["Expenses"]["Groceries"]]
        assert "March Groceries 1" in groceries
        assert "March Groceries 2" in groceries

    def test_get_transactions_by_month_empty(self, db_session, setup_test_data):
        """Test retrieving transactions for a month with no data."""
        # Test for a month with no data (January 2025)
        year, month = 2025, 1
        
        result = get_transactions_by_month_service(db_session, MOCK_USER, year, month)
        
        # Verify empty result
        assert result == {}

    def test_get_transactions_by_month_error(self, db_session):
        """Test error handling in get_transactions_by_month_service."""
        # Mock a database error
        with patch.object(db_session, 'query') as mock_query:
            mock_query.side_effect = SQLAlchemyError("Database error")
            
            # Test for exception
            with pytest.raises(HTTPException) as exc_info:
                get_transactions_by_month_service(db_session, MOCK_USER, 2025, 3)
            
            assert exc_info.value.status_code == 500
            assert "Error fetching transactions" in exc_info.value.detail

    def test_get_expense_totals_service(self, db_session, setup_test_data):
        """Test calculating expense totals for a specific month."""
        # Test for March 2025
        year, month = 2025, 3
        
        result = get_expense_totals_service(db_session, MOCK_USER, year, month)
        
        # Verify categories
        assert "Groceries" in result
        assert "Dining" in result
        assert "Housing" in result
        assert "Transportation" in result
        
        # Verify totals
        assert result["Groceries"] == 350.0  # 200 + 150
        assert result["Dining"] == 160.0  # 75 + 85
        assert result["Housing"] == 1500.0
        assert result["Transportation"] == 50.0
        
        # Income should not be included
        assert "Salary" not in result
        assert "Freelance" not in result

    def test_get_expense_totals_empty(self, db_session, setup_test_data):
        """Test expense totals for a month with no data."""
        # Test for a month with no data (January 2025)
        year, month = 2025, 1
        
        result = get_expense_totals_service(db_session, MOCK_USER, year, month)
        
        # Verify empty result
        assert result == {}

    def test_get_expense_totals_error(self, db_session):
        """Test error handling in get_expense_totals_service."""
        # Mock a database error
        with patch.object(db_session, 'query') as mock_query:
            mock_query.side_effect = SQLAlchemyError("Database error")
            
            # Test for exception
            with pytest.raises(HTTPException) as exc_info:
                get_expense_totals_service(db_session, MOCK_USER, 2025, 3)
            
            assert exc_info.value.status_code == 500
            assert "Error calculating expense totals" in exc_info.value.detail

    def test_get_totals_service(self, db_session, setup_test_data):
        """Test calculating income and expense totals for a specific month."""
        # Test for March 2025
        year, month = 2025, 3
        
        result = get_totals_service(db_session, MOCK_USER, year, month)
        
        # Verify structure
        assert "income" in result
        assert "expenses" in result
        
        # Verify totals
        assert result["income"] == 6000.0  # 5000 + 1000
        assert result["expenses"] == 2060.0  # 1500 + 350 + 160 + 50

    def test_get_totals_partial_data(self, db_session, setup_test_data):
        """Test totals for a month with only income or only expenses."""
        # May 2025 has only salary and rent
        year, month = 2025, 5
        
        result = get_totals_service(db_session, MOCK_USER, year, month)
        
        # Verify totals
        assert result["income"] == 5000.0
        assert result["expenses"] == 1500.0

    def test_get_totals_empty(self, db_session, setup_test_data):
        """Test totals for a month with no data."""
        # Test for a month with no data (January 2025)
        year, month = 2025, 1
        
        result = get_totals_service(db_session, MOCK_USER, year, month)
        
        # Verify zero totals
        assert result["income"] == 0
        assert result["expenses"] == 0

    def test_get_totals_error(self, db_session):
        """Test error handling in get_totals_service."""
        # Mock a database error
        with patch.object(db_session, 'query') as mock_query:
            mock_query.side_effect = SQLAlchemyError("Database error")
            
            # Test for exception
            with pytest.raises(HTTPException) as exc_info:
                get_totals_service(db_session, MOCK_USER, 2025, 3)
            
            assert exc_info.value.status_code == 500
            assert "Error calculating totals" in exc_info.value.detail

    def test_get_grouped_transactions_service(self, db_session, setup_test_data):
        """Test retrieving grouped transactions for a specific month."""
        # Test for March 2025
        year, month = 2025, 3
        
        result = get_grouped_transactions_service(db_session, MOCK_USER, year, month)
        
        # Verify structure - should be a list of section objects
        assert isinstance(result, list)
        
        # Find sections
        income_section = next((s for s in result if s["section"] == "Income"), None)
        expenses_section = next((s for s in result if s["section"] == "Expenses"), None)
        
        assert income_section is not None
        assert expenses_section is not None
        
        # Verify section totals
        assert income_section["total"] == 6000.0
        assert expenses_section["total"] == 2060.0
        
        # Verify categories in each section
        income_categories = {c["name"]: c for c in income_section["categories"]}
        expense_categories = {c["name"]: c for c in expenses_section["categories"]}
        
        assert "Salary" in income_categories
        assert "Freelance" in income_categories
        assert "Groceries" in expense_categories
        assert "Dining" in expense_categories
        assert "Housing" in expense_categories
        assert "Transportation" in expense_categories
        
        # Verify category totals
        assert income_categories["Salary"]["total"] == 5000.0
        assert income_categories["Freelance"]["total"] == 1000.0
        assert expense_categories["Groceries"]["total"] == 350.0
        assert expense_categories["Dining"]["total"] == 160.0
        assert expense_categories["Housing"]["total"] == 1500.0
        assert expense_categories["Transportation"]["total"] == 50.0
        
        # Verify transactions in categories
        assert len(income_categories["Salary"]["transactions"]) == 1
        assert len(income_categories["Freelance"]["transactions"]) == 1
        assert len(expense_categories["Groceries"]["transactions"]) == 2
        assert len(expense_categories["Dining"]["transactions"]) == 2
        assert len(expense_categories["Housing"]["transactions"]) == 1
        assert len(expense_categories["Transportation"]["transactions"]) == 1

    def test_get_grouped_transactions_empty(self, db_session, setup_test_data):
        """Test grouped transactions for a month with no data."""
        # Test for a month with no data (January 2025)
        year, month = 2025, 1
        
        result = get_grouped_transactions_service(db_session, MOCK_USER, year, month)
        
        # Verify empty result
        assert result == []

    def test_get_grouped_transactions_error(self, db_session):
        """Test error handling in get_grouped_transactions_service."""
        # Mock a database error
        with patch.object(db_session, 'query') as mock_query:
            mock_query.side_effect = SQLAlchemyError("Database error")
            
            # Test for exception
            with pytest.raises(HTTPException) as exc_info:
                get_grouped_transactions_service(db_session, MOCK_USER, 2025, 3)
            
            assert exc_info.value.status_code == 500
            assert "Error fetching and grouping transactions" in exc_info.value.detail

    @patch('app.services.transaction_reporting_service.pd.to_datetime')
    def test_get_history_service(self, mock_to_datetime, db_session, setup_test_data):
        """Test retrieving transaction history for the past six months."""
        # Mock today's date to be June 1, 2025 - this ensures our test data is within the 6-month window
        mock_date = pd.Timestamp('2025-06-01')
        mock_to_datetime.return_value = mock_date
        
        result = get_history_service(db_session, MOCK_USER)
        
        # Verify structure
        assert "March 2025" in result
        assert "April 2025" in result
        assert "May 2025" in result
        
        # Verify totals for March
        assert result["March 2025"]["income"] == 6000.0
        assert result["March 2025"]["expenses"] == 2060.0
        
        # Verify totals for April
        assert result["April 2025"]["income"] == 5000.0
        assert result["April 2025"]["expenses"] == 1745.0
        
        # Verify totals for May
        assert result["May 2025"]["income"] == 5000.0
        assert result["May 2025"]["expenses"] == 1500.0

    @patch('app.services.transaction_reporting_service.pd.to_datetime')
    def test_get_history_empty(self, mock_to_datetime, db_session):
        """Test history for a user with no data."""
        # Clear all transactions
        db_session.query(Transaction).delete()
        db_session.commit()
        
        # Set mock date
        mock_date = pd.Timestamp('2025-06-01')
        mock_to_datetime.return_value = mock_date
        
        result = get_history_service(db_session, MOCK_USER)
        
        # Verify empty result
        assert result == {}

    def test_get_history_error(self, db_session):
        """Test error handling in get_history_service."""
        # Mock a database error
        with patch.object(db_session, 'query') as mock_query:
            mock_query.side_effect = SQLAlchemyError("Database error")
            
            # Test for exception
            with pytest.raises(HTTPException) as exc_info:
                get_history_service(db_session, MOCK_USER)
            
            assert exc_info.value.status_code == 500
            assert "Error fetching transaction history" in exc_info.value.detail

    def test_get_transactions_range_service(self, db_session, setup_test_data):
        """Test retrieving the range of months with transactions."""
        result = get_transactions_range_service(db_session, MOCK_USER)
        
        # Verify structure - should be a list of months in YYYY-MM format
        assert isinstance(result, list)
        
        # Check order (most recent first)
        assert result[0] >= result[-1]
        
        # Check specific months
        months = set(result)
        assert "2025-03" in months
        assert "2025-04" in months
        assert "2025-05" in months

    def test_get_transactions_range_empty(self, db_session):
        """Test range for a user with no data."""
        # Clear all transactions
        db_session.query(Transaction).delete()
        db_session.commit()
        
        result = get_transactions_range_service(db_session, MOCK_USER)
        
        # Verify empty result
        assert result == []

    def test_get_transactions_range_error(self, db_session):
        """Test error handling in get_transactions_range_service."""
        # Mock a database error
        with patch.object(db_session, 'query') as mock_query:
            mock_query.side_effect = SQLAlchemyError("Database error")
            
            # Test for exception
            with pytest.raises(HTTPException) as exc_info:
                get_transactions_range_service(db_session, MOCK_USER)
            
            assert exc_info.value.status_code == 500
            assert "Error retrieving transaction range" in exc_info.value.detail

    def test_dialect_detection_for_transaction_range(self, db_session):
        """Test dialect detection in get_transactions_range_service."""
        # Test with mock engine inspection
        with patch('app.services.transaction_reporting_service.inspect') as mock_inspect:
            # Setup mock for SQLite
            mock_sqlite = MagicMock()
            mock_sqlite.dialect.name = 'sqlite'
            mock_inspect.return_value = mock_sqlite
            
            with patch.object(db_session, 'query') as mock_query:
                # Just to avoid actual DB calls
                mock_query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = []
                
                # Call with SQLite dialect
                get_transactions_range_service(db_session, MOCK_USER)
                
                # Verify SQLite function was used (strftime)
                mock_query.assert_called()
                args, kwargs = mock_query.call_args
                assert 'strftime' in str(args)
            
            # Setup mock for PostgreSQL
            mock_postgres = MagicMock()
            mock_postgres.dialect.name = 'postgresql'
            mock_inspect.return_value = mock_postgres
            
            with patch.object(db_session, 'query') as mock_query:
                # Just to avoid actual DB calls
                mock_query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = []
                
                # Call with PostgreSQL dialect
                get_transactions_range_service(db_session, MOCK_USER)
                
                # Verify PostgreSQL function was used (to_char)
                mock_query.assert_called()
                args, kwargs = mock_query.call_args
                assert 'to_char' in str(args)
