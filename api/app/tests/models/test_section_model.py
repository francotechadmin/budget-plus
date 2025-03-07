import pytest
from datetime import datetime
from app.models.models import Section, User

class TestSectionModel:
    def test_create_section(self, db_session):
        """Test creating a new section"""
        # First create a user
        user = User(
            id="auth0|section_test",
            name="Section Test User",
            email="section_test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a section
        section = Section(
            name="Test Section",
            description="Test section description",
            user_id=user.id
        )
        db_session.add(section)
        db_session.commit()
        db_session.refresh(section)
        
        assert section.id is not None
        assert section.name == "Test Section"
        assert section.description == "Test section description"
        assert section.user_id == "auth0|section_test"
        assert section.is_deleted == 0
        assert isinstance(section.created_at, datetime)
        assert isinstance(section.updated_at, datetime)
    
    def test_update_section(self, db_session):
        """Test updating a section"""
        # Create section first
        section = Section(
            name="Original Section Name",
            description="Original description",
            user_id="auth0|1234567890"  # Using the mocked user ID from conftest
        )
        db_session.add(section)
        db_session.commit()
        
        original_created_at = section.created_at
        
        # Update section
        section.name = "Updated Section Name"
        section.description = "Updated description"
        db_session.commit()
        db_session.refresh(section)
        
        assert section.name == "Updated Section Name"
        assert section.description == "Updated description"
        assert section.created_at == original_created_at
        assert section.updated_at >= original_created_at
    
    def test_soft_delete_section(self, db_session):
        """Test soft deleting a section"""
        # Create section
        section = Section(
            name="Section to Delete",
            description="Will be deleted",
            user_id="auth0|1234567890"
        )
        db_session.add(section)
        db_session.commit()
        section_id = section.id
        
        # Soft delete
        section.is_deleted = 1
        db_session.commit()
        
        # Section should still exist
        deleted_section = db_session.query(Section).filter(Section.id == section_id).first()
        assert deleted_section is not None
        assert deleted_section.is_deleted == 1
    
    def test_autoincrement_id(self, db_session):
        """Test that section IDs are auto-incremented"""
        # Create multiple sections
        section1 = Section(
            name="Section One",
            description="First section",
            user_id="auth0|1234567890"
        )
        db_session.add(section1)
        db_session.commit()
        id1 = section1.id
        
        section2 = Section(
            name="Section Two",
            description="Second section",
            user_id="auth0|1234567890"
        )
        db_session.add(section2)
        db_session.commit()
        id2 = section2.id
        
        assert id2 > id1
