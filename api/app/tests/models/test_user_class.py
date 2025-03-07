import pytest
from datetime import datetime
from app.models.models import User
from sqlalchemy.exc import IntegrityError

class TestUserModel:
    def test_create_user(self, db_session):
        """Test creating a new user"""
        user = User(
            id="auth0|test_create",
            name="Test User",
            email="test_create@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id == "auth0|test_create"
        assert user.name == "Test User"
        assert user.email == "test_create@example.com"
        assert user.is_admin == 0
        assert user.is_deleted == 0
        assert user.is_active == 1
        assert user.is_verified == 0
        assert user.is_locked == 0
        assert user.is_premium == 0
        assert user.is_subscribed == 0
        assert user.stripe_customer_id is None
        assert user.stripe_subscription_id is None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_unique_email_constraint(self, db_session):
        """Test that email must be unique"""
        # First user with email
        user1 = User(
            id="auth0|test_unique1",
            name="Test User 1",
            email="duplicate@example.com"
        )
        db_session.add(user1)
        db_session.commit()

        # Second user with same email should fail
        user2 = User(
            id="auth0|test_unique2",
            name="Test User 2",
            email="duplicate@example.com"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        # Rollback the failed transaction
        db_session.rollback()

    def test_update_user(self, db_session):
        """Test updating user information"""
        # Create a user first
        user = User(
            id="auth0|test_update",
            name="Original Name",
            email="update_test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Get creation timestamp for comparison
        original_created_at = user.created_at
        original_updated_at = user.updated_at
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Update the user
        user.name = "Updated Name"
        user.is_premium = 1
        db_session.commit()
        db_session.refresh(user)
        
        # Check updates
        assert user.name == "Updated Name"
        assert user.is_premium == 1
        assert user.created_at == original_created_at
        assert user.updated_at > original_updated_at

    def test_soft_delete_user(self, db_session):
        """Test soft deleting a user by setting is_deleted flag"""
        user = User(
            id="auth0|test_delete",
            name="Delete Test",
            email="delete_test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Soft delete
        user.is_deleted = 1
        user.is_active = 0
        db_session.commit()
        db_session.refresh(user)
        
        assert user.is_deleted == 1
        assert user.is_active == 0
        
        # User should still exist in database
        deleted_user = db_session.query(User).filter(User.id == "auth0|test_delete").first()
        assert deleted_user is not None
        assert deleted_user.is_deleted == 1