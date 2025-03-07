import pytest
from datetime import datetime, timedelta
from app.models.models import Budget, Category, User

class TestBudgetModel:
    def test_create_budget(self, db_session):
        """Test creating a new budget"""
        # Get an existing category
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        assert category is not None
        
        # Create a budget
        valid_from = datetime.now()
        valid_to = valid_from + timedelta(days=30)
        
        budget = Budget(
            user_id="auth0|1234567890",
            category_id=category.id,
            name="Monthly Test Budget",
            description="Budget for testing purposes",
            amount=1000.00,
            valid_from=valid_from,
            valid_to=valid_to
        )
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)
        
        assert budget.id is not None
        assert budget.user_id == "auth0|1234567890"
        assert budget.category_id == category.id
        assert budget.name == "Monthly Test Budget"
        assert budget.description == "Budget for testing purposes"
        assert budget.amount == 1000.00
        assert budget.version == 1
        assert budget.valid_from == valid_from
        assert budget.valid_to == valid_to
        assert budget.active == 1
        assert budget.is_deleted == 0
        assert isinstance(budget.created_at, datetime)
        assert isinstance(budget.updated_at, datetime)
    
    def test_update_budget(self, db_session):
        """Test updating a budget"""
        # Create a budget first
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        
        budget = Budget(
            user_id="auth0|1234567890",
            category_id=category.id,
            name="Original Budget",
            description="Original description",
            amount=500.00,
            valid_from=datetime.now(),
            valid_to=datetime.now() + timedelta(days=30)
        )
        db_session.add(budget)
        db_session.commit()
        
        original_created_at = budget.created_at
        original_version = budget.version
        
        # Update budget
        budget.name = "Updated Budget"
        budget.description = "Updated description"
        budget.amount = 750.00
        budget.version = budget.version + 1
        db_session.commit()
        db_session.refresh(budget)
        
        assert budget.name == "Updated Budget"
        assert budget.description == "Updated description"
        assert budget.amount == 750.00
        assert budget.version == original_version + 1
        assert budget.created_at == original_created_at
        assert budget.updated_at > original_created_at
    
    def test_soft_delete_budget(self, db_session):
        """Test soft deleting a budget"""
        # Create a budget to delete
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        
        budget = Budget(
            user_id="auth0|1234567890",
            category_id=category.id,
            name="Budget to Delete",
            description="Will be deleted",
            amount=300.00,
            valid_from=datetime.now(),
            valid_to=datetime.now() + timedelta(days=30)
        )
        db_session.add(budget)
        db_session.commit()
        budget_id = budget.id
        
        # Soft delete
        budget.is_deleted = 1
        budget.active = 0
        db_session.commit()
        
        # Budget should still exist
        deleted_budget = db_session.query(Budget).filter(Budget.id == budget_id).first()
        assert deleted_budget is not None
        assert deleted_budget.is_deleted == 1
        assert deleted_budget.active == 0
    
    def test_budget_with_no_end_date(self, db_session):
        """Test creating a budget with no end date (ongoing)"""
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        
        # Create budget with no end date
        budget = Budget(
            user_id="auth0|1234567890",
            category_id=category.id,
            name="Ongoing Budget",
            description="Budget with no end date",
            amount=200.00,
            valid_from=datetime.now(),
            valid_to=None  # No end date
        )
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)
        
        assert budget.valid_to is None
        
    def test_budget_relationships(self, db_session):
        """Test that budgets are properly related to users and categories"""
        # Create new user
        user = User(
            id="auth0|budget_rel_test",
            name="Budget Relationship Test",
            email="budget_rel@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Get existing category
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        
        # Create budget with relationships
        budget = Budget(
            user_id=user.id,
            category_id=category.id,
            name="Relationship Test Budget",
            description="Testing relationships",
            amount=450.00,
            valid_from=datetime.now()
        )
        db_session.add(budget)
        db_session.commit()
        
        # Query budget by relationships
        result = db_session.query(Budget).filter(
            Budget.user_id == user.id,
            Budget.category_id == category.id
        ).first()
        
        assert result is not None
        assert result.name == "Relationship Test Budget"
        assert result.user_id == user.id
        assert result.category_id == category.id
