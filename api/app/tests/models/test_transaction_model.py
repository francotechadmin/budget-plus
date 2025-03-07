import pytest
from datetime import datetime, date
from app.models.models import Transaction, Category, User

class TestTransactionModel:
    def test_create_transaction(self, db_session):
        """Test creating a new transaction"""
        # Get an existing category
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        assert category is not None
        
        # Create a transaction
        transaction = Transaction(
            user_id="auth0|1234567890",
            category_id=category.id,
            name="Test Purchase",
            description="Bought something for testing",
            date=date(2025, 3, 1),
            amount=123.45
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.user_id == "auth0|1234567890"
        assert transaction.category_id == category.id
        assert transaction.name == "Test Purchase"
        assert transaction.description == "Bought something for testing"
        assert transaction.date == date(2025, 3, 1)
        assert transaction.amount == 123.45
        assert transaction.is_indexed == 0
        assert transaction.is_deleted == 0
        assert transaction.is_imported == 0
        assert transaction.is_manual == 0
        assert transaction.is_linked == 0
        assert isinstance(transaction.created_at, datetime)
        assert isinstance(transaction.updated_at, datetime)
    
    def test_update_transaction(self, db_session):
        """Test updating a transaction"""
        # Create a transaction first
        old_category = db_session.query(Category).filter(Category.name == "Old Category").first()
        transaction = Transaction(
            user_id="auth0|1234567890",
            category_id=old_category.id,
            name="Original Transaction",
            description="Original description",
            date=date(2025, 2, 15),
            amount=50.00
        )
        db_session.add(transaction)
        db_session.commit()
        
        original_created_at = transaction.created_at
        
        # Find a different category for the update
        new_category = db_session.query(Category).filter(Category.name == "New Category").first()
        
        # Update transaction
        transaction.category_id = new_category.id
        transaction.name = "Updated Transaction"
        transaction.description = "Updated description"
        transaction.amount = 75.50
        transaction.is_manual = 1
        db_session.commit()
        db_session.refresh(transaction)
        
        assert transaction.category_id == new_category.id
        assert transaction.name == "Updated Transaction"
        assert transaction.description == "Updated description"
        assert transaction.amount == 75.50
        assert transaction.is_manual == 1
        assert transaction.created_at == original_created_at
        assert transaction.updated_at > original_created_at
    
    def test_soft_delete_transaction(self, db_session):
        """Test soft deleting a transaction"""
        # Create a transaction to delete
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        transaction = Transaction(
            user_id="auth0|1234567890",
            category_id=category.id,
            name="Transaction to Delete",
            description="Will be deleted",
            date=date(2025, 3, 2),
            amount=99.99
        )
        db_session.add(transaction)
        db_session.commit()
        transaction_id = transaction.id
        
        # Soft delete
        transaction.is_deleted = 1
        db_session.commit()
        
        # Transaction should still exist
        deleted_transaction = db_session.query(Transaction).filter(Transaction.id == transaction_id).first()
        assert deleted_transaction is not None
        assert deleted_transaction.is_deleted == 1
    
    def test_transaction_relationships(self, db_session):
        """Test that transactions are properly related to users and categories"""
        # Create new user
        user = User(
            id="auth0|tx_rel_test",
            name="Transaction Relationship Test",
            email="tx_rel@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Get existing category
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        
        # Create transaction with relationships
        transaction = Transaction(
            user_id=user.id,
            category_id=category.id,
            name="Relationship Test Transaction",
            description="Testing relationships",
            date=date(2025, 3, 3),
            amount=150.75
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Query transaction by relationships
        result = db_session.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.category_id == category.id
        ).first()
        
        assert result is not None
        assert result.name == "Relationship Test Transaction"
        assert result.user_id == user.id
        assert result.category_id == category.id
