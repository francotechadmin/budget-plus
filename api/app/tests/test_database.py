import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Test the get_db function separately since it doesn't require module reloading
class TestGetDb:
    def test_get_db_generator(self):
        """Test the get_db dependency function creates and closes a session."""
        # Import directly for this test only
        from app.database.database import get_db
        
        # Create a mock session
        mock_session = MagicMock()
        
        # Patch SessionLocal to return our mock
        with patch('app.database.database.SessionLocal', return_value=mock_session):
            # Get the generator
            db_generator = get_db()
            
            # Get the session from the generator
            db = next(db_generator)
            
            # Check it's our mock
            assert db is mock_session
            
            # Exhaust the generator to trigger the finally block
            try:
                next(db_generator)
            except StopIteration:
                pass
            
            # Verify close was called
            mock_session.close.assert_called_once()

# Test the Base class separately
class TestBaseClass:
    def test_base_class(self):
        """Test that the Base class is properly configured."""
        # Import directly for this test only
        from app.database.database import Base
        
        # Check Base is a DeclarativeBase (checking types directly)
        assert isinstance(Base, type)
        assert issubclass(Base, DeclarativeBase)
        
        # Create a model with Base - include primary key
        class TestModel(Base):
            __tablename__ = "test_model"
            id = Column(Integer, primary_key=True)
            name = Column(String)
        
        # Check the model has basic SQLAlchemy features
        assert hasattr(TestModel, "__tablename__")
        assert TestModel.__tablename__ == "test_model"
        assert hasattr(TestModel, "id")
        assert hasattr(TestModel, "name")

# Use a fixture to create a clean testing environment for each test
class TestDatabaseConfiguration:
    @pytest.fixture(autouse=True)
    def setup_module(self, monkeypatch):
        """Create a clean environment for each test with all dependencies mocked."""
        # Store original modules
        self.original_modules = sys.modules.copy()
        
        # Clear cached imports that might interfere
        for mod in list(sys.modules.keys()):
            if mod.startswith('app.database'):
                sys.modules.pop(mod, None)
        
        # Set up mocks
        self.mock_engine = MagicMock()
        self.mock_logger = MagicMock()
        
        # Patch before importing
        monkeypatch.setattr('sqlalchemy.create_engine', lambda *args, **kwargs: self.mock_engine)
        monkeypatch.setattr('app.utils.logger.get_logger', lambda *args, **kwargs: self.mock_logger)
        
        yield
        
        # Clean up modules to avoid cross-test contamination
        for mod in list(sys.modules.keys()):
            if mod not in self.original_modules:
                sys.modules.pop(mod, None)
            elif mod.startswith('app.database'):
                sys.modules[mod] = self.original_modules.get(mod)
    
    def test_database_env_variables(self, monkeypatch):
        """Test that environment variables are correctly used to build DB URL."""
        # Set custom environment variables
        monkeypatch.setenv('PG_HOST', 'test-host')
        monkeypatch.setenv('PG_DBNAME', 'test-db')
        monkeypatch.setenv('PG_USER', 'test-user')
        monkeypatch.setenv('PG_PASSWORD', 'test-password')
        monkeypatch.setenv('PG_PORT', '5433')
        
        # Import the module
        from app.database import database
        
        # Check the DB URL was constructed correctly
        expected_url = "postgresql://test-user:test-password@test-host:5433/test-db"
        assert database.DB_URL == expected_url
    
    def test_database_default_variables(self, monkeypatch):
        """Test that default environment values are used when not provided."""
        # Ensure environment variables are not set
        for var in ['PG_HOST', 'PG_DBNAME', 'PG_USER', 'PG_PASSWORD', 'PG_PORT']:
            monkeypatch.delenv(var, raising=False)
        
        # Import the module
        from app.database import database
        
        # Check default values are used
        expected_url = "postgresql://postgres:mysecretpassword@localhost:5432/postgres"
        assert database.DB_URL == expected_url
    
    def test_engine_creation_error(self, monkeypatch):
        """Test that errors during engine creation are properly handled."""
        # Replace create_engine with one that raises an exception
        def mock_create_engine_error(*args, **kwargs):
            raise Exception("Test DB connection error")
        
        monkeypatch.setattr('sqlalchemy.create_engine', mock_create_engine_error)
        
        # Import the module and check for exception
        with pytest.raises(Exception) as exc_info:
            from app.database import database
        
        # Verify the error was logged
        assert "Test DB connection error" in str(exc_info.value)
        assert self.mock_logger.error.called
    
    def test_engine_echo_setting(self, monkeypatch):
        """Test that the engine is created with echo=True."""
        # Set up a mock for create_engine that captures the arguments
        create_engine_args = {}
        
        def mock_create_engine(*args, **kwargs):
            create_engine_args.update(kwargs)
            return self.mock_engine
        
        # Replace the monkeypatch to use our argument-capturing mock
        monkeypatch.setattr('sqlalchemy.create_engine', mock_create_engine)
        
        # Import the module
        from app.database import database
        
        # Check that create_engine was called with echo=True
        assert 'echo' in create_engine_args
        assert create_engine_args['echo'] is True
    
    def test_sessionmaker_configuration(self, monkeypatch):
        """Test that SessionLocal is configured correctly."""
        # Mock sessionmaker
        mock_sessionmaker = MagicMock()
        mock_sessionmaker.return_value = MagicMock()
        monkeypatch.setattr('sqlalchemy.orm.sessionmaker', mock_sessionmaker)
        
        # Import the module
        from app.database import database
        
        # Check sessionmaker was called with the right arguments
        mock_sessionmaker.assert_called_once()
        kwargs = mock_sessionmaker.call_args[1]
        assert kwargs['autocommit'] is False
        assert kwargs['autoflush'] is False
        assert 'bind' in kwargs
    
    def test_logger_calls(self):
        """Test that the logger is used correctly during database setup."""
        # Import the module
        from app.database import database
        
        # Verify debug logs
        assert self.mock_logger.debug.call_count >= 2
        
        # Get all debug call arguments
        debug_calls = [call[0][0] for call in self.mock_logger.debug.call_args_list]
        
        # Check for expected log messages
        assert any('Connecting to database' in msg for msg in debug_calls)
        assert any('successfully' in msg for msg in debug_calls)