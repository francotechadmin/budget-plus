import pytest
from datetime import datetime
from app.models.models import Category, Section, User

class TestCategoryModel:
    def test_create_category(self, db_session):
        """Test creating a new category"""
        # Get the test section that was created in the fixture
        section = db_session.query(Section).filter(Section.name == "Test Section").first()
        assert section is not None
        
        # Create a category
        category = Category(
            name="New Test Category",
            description="New test category description",
            section_id=section.id,
            user_id="auth0|1234567890"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        assert category.id is not None
        assert category.name == "New Test Category"
        assert category.description == "New test category description"
        assert category.section_id == section.id
        assert category.user_id == "auth0|1234567890"
        assert category.is_deleted == 0
        assert category.is_active == 1
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)
    
    def test_update_category(self, db_session):
        """Test updating a category"""
        # Find existing category from fixture
        category = db_session.query(Category).filter(Category.name == "Test Category").first()
        assert category is not None
        
        original_created_at = category.created_at
        
        # Update category
        category.name = "Updated Category Name"
        category.description = "Updated description"
        db_session.commit()
        db_session.refresh(category)
        
        assert category.name == "Updated Category Name"
        assert category.description == "Updated description"
        assert category.created_at == original_created_at
        assert category.updated_at > original_created_at
    
    def test_soft_delete_category(self, db_session):
        """Test soft deleting a category"""
        # Find existing category for deletion
        category = db_session.query(Category).filter(Category.name == "Test Delete").first()
        assert category is not None
        category_id = category.id
        
        # Soft delete
        category.is_deleted = 1
        category.is_active = 0
        db_session.commit()
        
        # Category should still exist
        deleted_category = db_session.query(Category).filter(Category.id == category_id).first()
        assert deleted_category is not None
        assert deleted_category.is_deleted == 1
        assert deleted_category.is_active == 0
    
    def test_category_relationships(self, db_session):
        """Test that categories are properly related to users and sections"""
        # Get existing section
        section = db_session.query(Section).filter(Section.name == "Test Section").first()
        
        # Create new user for this test
        user = User(
            id="auth0|category_rel_test",
            name="Category Relationship Test",
            email="category_rel@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create category with relationships
        category = Category(
            name="Relationship Test Category",
            description="Testing relationships",
            user_id=user.id,
            section_id=section.id
        )
        db_session.add(category)
        db_session.commit()
        
        # Query category by relationships
        result = db_session.query(Category).filter(
            Category.user_id == user.id,
            Category.section_id == section.id
        ).first()
        
        assert result is not None
        assert result.name == "Relationship Test Category"
        assert result.user_id == user.id
        assert result.section_id == section.id
