import pytest
from datetime import datetime, date
from app.models.models import CategoryCorrections, Transaction, Category, User

class TestCategoryCorrectionsModel:
    def test_create_category_correction(self, db_session):
        """Test creating a new category correction"""
        # Get existing categories
        old_category = db_session.query(Category).filter(Category.name == "Old Category").first()
        new_category = db_session.query(Category).filter(Category.name == "New Category").first()
        assert old_category is not None
        assert new_category is not None
        
        # Create a transaction first
        transaction = Transaction(
            user_id="auth0|1234567890",
            category_id=old_category.id,
            name="Transaction for Correction",
            description="Will be corrected",
            date=date(2025, 3, 5),
            amount=45.67
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        # Create a category correction
        correction = CategoryCorrections(
            user_id="auth0|1234567890",
            transaction_id=transaction.id,
            old_category_id=old_category.id,
            new_category_id=new_category.id
        )
        db_session.add(correction)
        db_session.commit()
        db_session.refresh(correction)
        
        assert correction.id is not None
        assert correction.user_id == "auth0|1234567890"
        assert correction.transaction_id == transaction.id
        assert correction.old_category_id == old_category.id
        assert correction.new_category_id == new_category.id
        assert isinstance(correction.created_at, datetime)
        assert isinstance(correction.updated_at, datetime)
        
        # Also update the transaction's category
        transaction.category_id = new_category.id
        db_session.commit()
        db_session.refresh(transaction)
        
        assert transaction.category_id == new_category.id
    
    def test_correction_relationships(self, db_session):
        """Test that corrections are properly related to users, transactions, and categories"""
        # Create new user
        user = User(
            id="auth0|correction_rel_test",
            name="Correction Relationship Test",
            email="correction_rel@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Get existing categories
        old_category = db_session.query(Category).filter(Category.name == "Old Category").first()
        new_category = db_session.query(Category).filter(Category.name == "New Category").first()
        
        # Create transaction
        transaction = Transaction(
            user_id=user.id,
            category_id=old_category.id,
            name="Transaction for Relationship Test",
            description="Testing correction relationships",
            date=date(2025, 3, 6),
            amount=78.90
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Create correction with relationships
        correction = CategoryCorrections(
            user_id=user.id,
            transaction_id=transaction.id,
            old_category_id=old_category.id,
            new_category_id=new_category.id
        )
        db_session.add(correction)
        db_session.commit()
        
        # Query correction by relationships
        result = db_session.query(CategoryCorrections).filter(
            CategoryCorrections.user_id == user.id,
            CategoryCorrections.transaction_id == transaction.id
        ).first()
        
        assert result is not None
        assert result.user_id == user.id
        assert result.transaction_id == transaction.id
        assert result.old_category_id == old_category.id
        assert result.new_category_id == new_category.id
        
    def test_multiple_corrections_for_transaction(self, db_session):
        """Test that multiple corrections can be made for a single transaction"""
        # Get categories
        category1 = db_session.query(Category).filter(Category.name == "Test Category").first()
        category2 = db_session.query(Category).filter(Category.name == "Old Category").first()
        category3 = db_session.query(Category).filter(Category.name == "New Category").first()
        
        # Create transaction
        transaction = Transaction(
            user_id="auth0|1234567890",
            category_id=category1.id,
            name="Multiple Corrections Transaction",
            description="Will have multiple corrections",
            date=date(2025, 3, 7),
            amount=100.00
        )
        db_session.add(transaction)
        db_session.commit()
        
        # First correction
        correction1 = CategoryCorrections(
            user_id="auth0|1234567890",
            transaction_id=transaction.id,
            old_category_id=category1.id,
            new_category_id=category2.id
        )
        db_session.add(correction1)
        db_session.commit()
        
        # Update transaction category
        transaction.category_id = category2.id
        db_session.commit()
        
        # Second correction
        correction2 = CategoryCorrections(
            user_id="auth0|1234567890",
            transaction_id=transaction.id,
            old_category_id=category2.id,
            new_category_id=category3.id
        )
        db_session.add(correction2)
        db_session.commit()
        
        # Update transaction category again
        transaction.category_id = category3.id
        db_session.commit()
        
        # Query corrections for this transaction
        corrections = db_session.query(CategoryCorrections).filter(
            CategoryCorrections.transaction_id == transaction.id
        ).order_by(CategoryCorrections.created_at).all()
        
        assert len(corrections) == 2
        assert corrections[0].old_category_id == category1.id
        assert corrections[0].new_category_id == category2.id
        assert corrections[1].old_category_id == category2.id
        assert corrections[1].new_category_id == category3.id
