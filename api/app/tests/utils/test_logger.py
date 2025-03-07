import pytest
import os
import logging
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
from io import StringIO
from app.utils.logger import (
    setup_logger,
    get_logger,
    log_exception,
    configure_module_loggers,
    setup_exception_logging
)

class TestLogger:
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def captured_logs(self):
        """Fixture to capture log output for testing."""
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        old_handlers = logger.handlers.copy()
        logger.handlers.clear()
        logger.addHandler(handler)
        
        yield log_capture
        
        # Restore original handlers
        logger.handlers.clear()
        for h in old_handlers:
            logger.addHandler(h)

    def test_setup_logger_defaults(self, temp_log_dir):
        """Test logger setup with default parameters."""
        logger = setup_logger(name='test_default', log_dir=temp_log_dir)
        
        # Check logger configuration
        assert logger.name == 'test_default'
        assert logger.level == logging.DEBUG  # Default is DEBUG
        
        # Check handlers
        assert len(logger.handlers) == 1  # Default has only console handler
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logger_with_custom_level(self, temp_log_dir):
        """Test logger setup with custom log level."""
        logger = setup_logger(name='test_level', log_level='ERROR', log_dir=temp_log_dir)
        
        assert logger.level == logging.ERROR
        assert logger.handlers[0].level == logging.ERROR

    def test_setup_logger_with_file_handler(self, temp_log_dir):
        """Test logger setup with file handler."""
        logger = setup_logger(
            name='test_file',
            log_dir=temp_log_dir,
            log_handlers=['console', 'file']
        )
        
        # Check handlers
        assert len(logger.handlers) == 2
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], logging.handlers.RotatingFileHandler)
        
        # Verify file was created
        log_files = [f for f in os.listdir(temp_log_dir) if f.startswith('test_file_')]
        assert len(log_files) == 1

    def test_setup_logger_max_file_size(self, temp_log_dir):
        """Test logger setup with custom max file size."""
        max_size = 2  # 2 MB
        logger = setup_logger(
            name='test_size',
            log_dir=temp_log_dir,
            log_handlers=['file'],
            max_file_size_mb=max_size
        )
        
        file_handler = logger.handlers[0]
        assert isinstance(file_handler, logging.handlers.RotatingFileHandler)
        assert file_handler.maxBytes == max_size * 1024 * 1024

    def test_setup_logger_backup_count(self, temp_log_dir):
        """Test logger setup with custom backup count."""
        backup_count = 3
        logger = setup_logger(
            name='test_backup',
            log_dir=temp_log_dir,
            log_handlers=['file'],
            backup_count=backup_count
        )
        
        file_handler = logger.handlers[0]
        assert isinstance(file_handler, logging.handlers.RotatingFileHandler)
        assert file_handler.backupCount == backup_count

    @patch.dict(os.environ, {"LOG_LEVEL": "WARNING"})
    def test_setup_logger_env_level(self, temp_log_dir):
        """Test logger respects LOG_LEVEL environment variable."""
        logger = setup_logger(name='test_env_level', log_dir=temp_log_dir)
        
        assert logger.level == logging.WARNING

    def test_get_logger_defaults(self):
        """Test get_logger with default parameters."""
        with patch('app.utils.logger.setup_logger') as mock_setup:
            mock_setup.return_value = MagicMock()
            
            logger = get_logger()
            
            # Check that setup_logger was called with correct default parameters
            mock_setup.assert_called_once()
            call_args = mock_setup.call_args[1]
            
            # In default development mode, log level should be DEBUG
            assert call_args['log_level'] == 'DEBUG'

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_get_logger_production(self):
        """Test get_logger in production environment."""
        with patch('app.utils.logger.setup_logger') as mock_setup:
            mock_setup.return_value = MagicMock()
            
            logger = get_logger()
            
            # Check that setup_logger was called with production log level
            call_args = mock_setup.call_args[1]
            assert call_args['log_level'] == 'WARNING'

    @patch.dict(os.environ, {"APP_ENV": "testing"})
    def test_get_logger_testing(self):
        """Test get_logger in testing environment."""
        with patch('app.utils.logger.setup_logger') as mock_setup:
            mock_setup.return_value = MagicMock()
            
            logger = get_logger()
            
            # Check that setup_logger was called with testing log level
            call_args = mock_setup.call_args[1]
            assert call_args['log_level'] == 'INFO'

    def test_get_logger_custom_name(self):
        """Test get_logger with custom name."""
        with patch('app.utils.logger.setup_logger') as mock_setup:
            mock_setup.return_value = MagicMock()
            
            logger = get_logger(name='custom_logger')
            
            # Check that setup_logger was called with correct name
            call_args = mock_setup.call_args[1]
            assert call_args['name'] == 'custom_logger'

    def test_get_logger_custom_environment(self):
        """Test get_logger with custom environment."""
        with patch('app.utils.logger.setup_logger') as mock_setup:
            mock_setup.return_value = MagicMock()
            
            logger = get_logger(environment='production')
            
            # Check that setup_logger was called with production log level
            call_args = mock_setup.call_args[1]
            assert call_args['log_level'] == 'WARNING'

    def test_log_exception(self, captured_logs):
        """Test log_exception functionality."""
        logger = logging.getLogger('test_exception')
        logger.setLevel(logging.ERROR)
        
        # Create an exception and log it
        try:
            raise ValueError("Test exception")
        except Exception as e:
            log_exception(logger, e, {'context': 'test', 'user_id': '123'})
            
        # Check that exception and context were logged
        log_output = captured_logs.getvalue()
        assert "Exception occurred: Test exception" in log_output
        assert "Additional Context:" in log_output
        assert "context: test" in log_output
        assert "user_id: 123" in log_output

    def test_configure_module_loggers(self):
        """Test configure_module_loggers function."""
        with patch('app.utils.logger.get_logger') as mock_get_logger:
            mock_get_logger.return_value = MagicMock()
            
            loggers = configure_module_loggers()
            
            # Check that get_logger was called for each module
            assert mock_get_logger.call_count == 3
            assert set(loggers.keys()) == {'transaction_service', 'user_service', 'authentication'}

    def test_setup_exception_logging(self):
        """Test setup_exception_logging function."""
        original_excepthook = sys.excepthook
        
        try:
            with patch('app.utils.logger.get_logger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                # Setup exception logging
                setup_exception_logging()
                
                # Verify excepthook was replaced
                assert sys.excepthook != original_excepthook
                
                # Simulate an exception to test the hook
                try:
                    exc_type, exc_value, tb = ValueError, ValueError("Test hook"), None
                    sys.excepthook(exc_type, exc_value, tb)
                    
                    # Check that logger.critical was called
                    mock_logger.critical.assert_called_once()
                    # First position argument should be "Uncaught exception"
                    assert mock_logger.critical.call_args[0][0] == "Uncaught exception"
                    # Check that exc_info was passed
                    assert mock_logger.critical.call_args[1]['exc_info'][0] == ValueError
                finally:
                    # Restore original excepthook for other tests
                    sys.excepthook = original_excepthook
        finally:
            # Make sure excepthook is always restored
            sys.excepthook = original_excepthook

    def test_logger_actual_output(self):
        """Test actual logger output."""
        # Create a StringIO object to capture log output
        captured_output = StringIO()
        
        # Create a handler that writes to our StringIO
        test_handler = logging.StreamHandler(captured_output)
        test_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        test_handler.setFormatter(formatter)
        
        # Create logger and add our handler
        logger = logging.getLogger('output_test')
        logger.setLevel(logging.DEBUG)
        # Clear any existing handlers
        logger.handlers.clear()
        logger.addHandler(test_handler)
        
        # Log some messages
        logger.info("Info message")
        logger.debug("Debug message")
        logger.warning("Warning message")
            
        # Check the captured output
        output = captured_output.getvalue()
        assert "INFO - Info message" in output
        assert "DEBUG - Debug message" in output
        assert "WARNING - Warning message" in output

    def test_duplicate_logger_setup(self, temp_log_dir):
        """Test that setting up logger with same name doesn't duplicate handlers."""
        # Setup logger first time
        logger1 = setup_logger(name='dup_test', log_dir=temp_log_dir)
        handler_count = len(logger1.handlers)
        
        # Setup again with same name
        logger2 = setup_logger(name='dup_test', log_dir=temp_log_dir)
        
        # Should be same logger instance
        assert logger1 is logger2
        # Should have same number of handlers (not doubled)
        assert len(logger2.handlers) == handler_count