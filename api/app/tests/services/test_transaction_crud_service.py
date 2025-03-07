import pytest
import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.models.models import Transaction, Category, Section, CategoryCorrections
from app.schemas.schemas import NewTransactionRequest, UpdateTransactionRequest
from app.services.transaction_crud_service import (
    get_all_transactions,
    create_transaction,
    update_transaction_category,
    delete_transaction_by_id
)

# Mock user for testing
MOCK_USER = {"sub": "auth0|1234567890", "email": "test@example.com"}

class TestTransactionService:
    
    def test_get_all_transactions(self, db_session):
        """Test retrieving all transactions for a user."""
        # Setup: Create test data
        section = db_session.query(Section).filter(Section.name == "Test Section", Section.user_id == MOCK_USER["sub"]).first()
        category = db_session.query(Category).filter(Category.name == "Test Category", Category.user_id == MOCK_USER["sub"]).first()
        
        # Clear existing transactions
        db_session.query(Transaction).filter(Transaction.user_id == MOCK_USER["sub"]).delete()
        db_session.commit()
        
        # Create test transactions
        transactions = [
            Transaction(
                user_id=MOCK_USER["sub"],
                description=f"Test transaction {i}",
                date=datetime.date(2025, 3, i+1),
                amount=100.0 * (i+1),
                category_id=category.id,
                is_deleted=0
            )
            for i in range(3)
        ]
        for txn in transactions:
            db_session.add(txn)
        db_session.commit()
        
        # Execute the function
        result = get_all_transactions(db_session, MOCK_USER)
        
        # Assertions
        assert len(result) == 3
        # Check for expected fields in response
        for txn in result:
            assert "id" in txn
            assert "description" in txn
            assert "date" in txn
            assert "amount" in txn
            assert "category" in txn
            assert "section" in txn
        
        # Check ordering (most recent first)
        assert result[0]["date"] > result[1]["date"]
        assert result[1]["date"] > result[2]["date"]
    
    def test_get_all_transactions_empty(self, db_session):
        """Test retrieving transactions when there are none."""
        # Setup: Clear any existing transactions
        db_session.query(Transaction).filter(Transaction.user_id == MOCK_USER["sub"]).delete()
        db_session.commit()
        
        # Execute the function
        result = get_all_transactions(db_session, MOCK_USER)
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_all_transactions_error(self, db_session):
        """Test error handling when retrieving transactions."""
        # Setup: Mock an exception in the database query
        with patch("sqlalchemy.orm.Session.query") as mock_query:
            mock_query.side_effect = SQLAlchemyError("Database error")
            
            # Execute and assert
            with pytest.raises(HTTPException) as exc_info:
                get_all_transactions(db_session, MOCK_USER)
            
            assert exc_info.value.status_code == 500
            assert "Error retrieving transactions" in exc_info.value.detail
    
    def test_create_transaction_with_category(self, db_session):
        """Test creating a transaction with a specified category."""
        # Setup: Ensure category exists
        section = db_session.query(Section).filter(Section.name == "Test Section").first()
        
        category_name = "Test Category"
        category = db_session.query(Category).filter(Category.name == category_name).first()
        
        # Create transaction request
        transaction_request = NewTransactionRequest(
            description="Test transaction",
            date=datetime.date(2025, 3, 15),
            amount=150.0,
            category=category_name
        )
        
        # Execute the function
        result = create_transaction(db_session, MOCK_USER, transaction_request)
        
        # Assertions
        assert result.id is not None
        assert result.description == "Test transaction"
        assert result.date == datetime.date(2025, 3, 15)
        assert result.amount == 150.0
        assert result.category_id == category.id
        assert result.is_manual == 1
        
        # Verify DB state
        db_txn = db_session.query(Transaction).filter(Transaction.id == result.id).first()
        assert db_txn is not None
    
    @patch("app.services.transaction_crud_service.predict_category")
    def test_create_transaction_without_category(self, mock_predict, db_session):
        """Test creating a transaction without a specified category (should use prediction)."""
        # Setup: Ensure categories exist
        section = Section(
            name="Test Section",
            user_id=MOCK_USER["sub"]
        )
        db_session.add(section)
        db_session.commit()
        
        predicted_category = "Predicted Category"
        category = Category(
            name=predicted_category,
            description="Predicted category",
            section_id=section.id,
            user_id=MOCK_USER["sub"]
        )
        db_session.add(category)
        db_session.commit()

        # Setup mock
        mock_predict.return_value = predicted_category
        
        # Create transaction request without category
        transaction_request = NewTransactionRequest(
            description="Predictable transaction",
            date=datetime.date(2025, 3, 16),
            amount=200.0,
            category=None
        )
        
        # Execute the function
        result = create_transaction(db_session, MOCK_USER, transaction_request)
        
        # Assertions
        assert result.id is not None
        assert result.description == "Predictable transaction"
        assert result.category_id == category.id
        
        # Verify prediction was called
        mock_predict.assert_called_once_with("Predictable transaction")
    
    @patch("app.services.transaction_crud_service.predict_category")
    def test_create_transaction_fallback_to_uncategorized(self, mock_predict, db_session):
        """Test creating a transaction when prediction fails to find a category."""
        # Setup: Ensure categories exist
        section = db_session.query(Section).filter(Section.name == "Test Section").first()
        
        # Create Uncategorized category
        uncategorized = db_session.query(Category).filter(Category.name == "Uncategorized").first()
        
        # Setup mock to return a non-existent category
        mock_predict.return_value = "NonExistentCategory"
        
        # Create transaction request without category
        transaction_request = NewTransactionRequest(
            description="Uncategorized transaction",
            date=datetime.date(2025, 3, 17),
            amount=300.0,
            category=None
        )
        
        # Execute the function
        result = create_transaction(db_session, MOCK_USER, transaction_request)
        
        # Assertions
        assert result.id is not None
        assert result.category_id == uncategorized.id
    
    def test_create_transaction_database_error(self, db_session):
        """Test error handling during transaction creation."""
        # Setup: Mock commit to raise an exception
        with patch.object(db_session, 'commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Database error")
            
            # Also patch rollback to verify it was called
            with patch.object(db_session, 'rollback') as mock_rollback:
                # Create a simple transaction request
                transaction_request = NewTransactionRequest(
                    description="Error transaction",
                    date=datetime.date(2025, 3, 18),
                    amount=400.0,
                    category="Test Category"
                )
                
                # Execute and assert
                with pytest.raises(HTTPException) as exc_info:
                    create_transaction(db_session, MOCK_USER, transaction_request)
                
                assert exc_info.value.status_code == 500
                assert "Error adding transaction" in exc_info.value.detail
                
                # Verify rollback was called
                mock_rollback.assert_called_once()
    
    def test_update_transaction_category(self, db_session):
        """Test updating the category of a transaction."""
        # clear existing transactions
        db_session.query(Transaction).filter(Transaction.user_id == MOCK_USER["sub"]).delete()
        db_session.query(Category).filter(Category.user_id == MOCK_USER["sub"]).delete()
        db_session.query(Section).filter(Section.user_id == MOCK_USER["sub"]).delete()
        db_session.commit()

        # Setup: Create test data
        section = Section(
            name="Test Section",
            user_id=MOCK_USER["sub"]
        )
        db_session.add(section)
        db_session.commit()
        
        old_category = Category(
            name="Old Category",
            description="Initial category",
            section_id=section.id,
            user_id=MOCK_USER["sub"]
        )
        db_session.add(old_category)
        db_session.commit()
        
        new_category = Category(
            name="New Category",
            description="Updated category",
            section_id=section.id,
            user_id=MOCK_USER["sub"]
        )
        db_session.add(new_category)
        db_session.commit()
        
        # Create a transaction to update
        txn = Transaction(
            user_id=MOCK_USER["sub"],
            description="Transaction to update",
            date=datetime.date(2025, 3, 19),
            amount=500.0,
            category_id=old_category.id,
            is_deleted=0
        )
        print("tran cat id", txn.category_id)
        db_session.add(txn)
        db_session.commit()
        db_session.refresh(txn)
        
        # Create update request
        update_request = UpdateTransactionRequest(
            transaction_id=txn.id,
            category="New Category"
        )
        
        # Execute the function
        result = update_transaction_category(db_session, MOCK_USER, update_request)
        print("result", result)
        
        # Assertions
        assert result["id"] == txn.id
        assert result["category"] == "New Category"
        
        # Verify DB state
        updated_txn = db_session.query(Transaction).filter(Transaction.id == txn.id).first()
        assert updated_txn.category_id == new_category.id
        
        # Verify correction was recorded - get the actual fields that exist
        correction = db_session.query(CategoryCorrections).filter(
            CategoryCorrections.transaction_id == txn.id
        ).first()
        assert correction is not None

        # log the correction fields
        print(correction.old_category_id)
        print(correction.new_category_id)
        
        # Update assertions to match the actual fields in your model
        # This fixes the assertion about column count
        assert correction.old_category_id == old_category.id
        assert correction.new_category_id == new_category.id
    
    def test_update_transaction_not_found(self, db_session):
        """Test updating a non-existent transaction."""
        # Create update request with non-existent ID
        update_request = UpdateTransactionRequest(
            transaction_id=999999,
            category="New Category"
        )
        
        # Execute and assert
        with pytest.raises(HTTPException) as exc_info:
            update_transaction_category(db_session, MOCK_USER, update_request)
        
        assert exc_info.value.status_code == 404
        assert "Transaction not found" in exc_info.value.detail
    
    def test_update_transaction_category_not_found(self, db_session):
        """Test updating to a non-existent category."""
        # Setup: Create a transaction
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        txn = Transaction(
            user_id=MOCK_USER["sub"],
            description="Transaction with invalid category update",
            date=datetime.date(2025, 3, 20),
            amount=600.0,
            category_id=category.id,
            is_deleted=0
        )
        db_session.add(txn)
        db_session.commit()
        db_session.refresh(txn)
        
        # Create update request with non-existent category
        update_request = UpdateTransactionRequest(
            transaction_id=txn.id,
            category="NonExistentCategory"
        )
        
        # Execute and assert
        with pytest.raises(HTTPException) as exc_info:
            update_transaction_category(db_session, MOCK_USER, update_request)
        
        assert exc_info.value.status_code == 404
        assert "Category not found" in exc_info.value.detail
    
    def test_update_transaction_database_error(self, db_session):
        """Test error handling during transaction update."""
        # Setup: Create test data
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        new_category = db_session.query(Category).filter(Category.name == "New Category").first()
        
        txn = Transaction(
            user_id=MOCK_USER["sub"],
            description="Transaction with update error",
            date=datetime.date(2025, 3, 21),
            amount=700.0,
            category_id=category.id,
            is_deleted=0
        )
        db_session.add(txn)
        db_session.commit()
        db_session.refresh(txn)
        
        # Create update request
        update_request = UpdateTransactionRequest(
            transaction_id=txn.id,
            category="New Category"
        )
        
        # Mock commit to raise an exception
        with patch.object(db_session, 'commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Database error")
            
            # Execute and assert
            with pytest.raises(HTTPException) as exc_info:
                update_transaction_category(db_session, MOCK_USER, update_request)
            
            assert exc_info.value.status_code == 500
            assert "Error recording category correction" in exc_info.value.detail
    
    def test_delete_transaction(self, db_session):
        """Test deleting a transaction (soft delete)."""
        # Setup: Create a transaction to delete
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        txn = Transaction(
            user_id=MOCK_USER["sub"],
            description="Transaction to delete",
            date=datetime.date(2025, 3, 22),
            amount=800.0,
            category_id=category.id,
            is_deleted=0
        )
        db_session.add(txn)
        db_session.commit()
        db_session.refresh(txn)
        
        # Mock get_all_transactions to avoid dependency
        with patch("app.services.transaction_crud_service.get_all_transactions") as mock_get_all:
            mock_get_all.return_value = []
            
            # Execute the function
            result = delete_transaction_by_id(db_session, MOCK_USER, txn.id)
            
            # Verify get_all_transactions was called
            mock_get_all.assert_called_once()
            
            # Verify DB state (soft delete)
            deleted_txn = db_session.query(Transaction).filter(Transaction.id == txn.id).first()
            assert deleted_txn.is_deleted == 1
    
    def test_delete_transaction_not_found(self, db_session):
        """Test deleting a non-existent transaction."""
        # Execute and assert
        with pytest.raises(HTTPException) as exc_info:
            delete_transaction_by_id(db_session, MOCK_USER, 999999)
        
        assert exc_info.value.status_code == 404
        assert "Transaction not found" in exc_info.value.detail
    
    def test_delete_transaction_database_error(self, db_session):
        """Test error handling during transaction deletion."""
        # Setup: Create a transaction to delete
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        txn = Transaction(
            user_id=MOCK_USER["sub"],
            description="Transaction with delete error",
            date=datetime.date(2025, 3, 23),
            amount=900.0,
            category_id=category.id,
            is_deleted=0
        )
        db_session.add(txn)
        db_session.commit()
        db_session.refresh(txn)
        
        # Mock commit to raise an exception
        with patch.object(db_session, 'commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Database error")
            
            # Execute and assert
            with pytest.raises(HTTPException) as exc_info:
                delete_transaction_by_id(db_session, MOCK_USER, txn.id)
            
            assert exc_info.value.status_code == 500
            assert "Error deleting transaction" in exc_info.value.detail