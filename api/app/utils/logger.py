import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name: str = 'app_logger', 
                 log_level: str = None, 
                 log_dir: str = 'logs', 
                 max_file_size_mb: int = 10, 
                 backup_count: int = 5,
                 log_handlers: list = ['console']
                 ):
    """
    Configures a logger with console and file handlers.
    
    Args:
        name (str): Name of the logger
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir (str): Directory to store log files
        max_file_size_mb (int): Maximum log file size in megabytes
        backup_count (int): Number of backup log files to keep
    
    Returns:
        logging.Logger: Configured logger
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    if 'console' in log_handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler with Rotation
    if 'file' in log_handlers:
        log_filename = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            log_filename, 
            maxBytes=max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Environment-specific logger configurations
def get_logger(name: str = None, environment: str = None):
    """
    Returns a logger based on the environment.
    
    Args:
        name (str): Name of the logger (defaults to module name)
        environment (str): Environment type (development, production, testing)
    
    Returns:
        logging.Logger: Configured logger
    """
    # Default environment detection
    if environment is None:
        environment = os.getenv('APP_ENV', 'development').lower()

    # Environment-specific log levels
    env_log_levels = {
        'development': 'DEBUG',
        'production': 'WARNING',
        'testing': 'INFO'
    }

    # Get log level for environment
    log_level = env_log_levels.get(environment, 'INFO')

    # If no name provided, use the module name
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = inspect.getmodule(frame).__name__

    return setup_logger(
        name=name, 
        log_level=log_level,
        log_dir=os.path.join(os.getcwd(), 'logs')
    )

# Example usage in a module
# logger = get_logger()
# logger.info("This is an informational message")
# logger.debug("This is a debug message")
# logger.error("This is an error message")

# Utility function to log exceptions
def log_exception(logger, e: Exception, additional_info: dict = None):
    """
    Logs an exception with optional additional context.
    
    Args:
        logger (logging.Logger): Logger to use
        e (Exception): Exception to log
        additional_info (dict): Optional additional context
    """
    logger.error(f"Exception occurred: {str(e)}", exc_info=True)
    
    if additional_info:
        logger.error("Additional Context:")
        for key, value in additional_info.items():
            logger.error(f"{key}: {value}")

# Example configuration for different modules
def configure_module_loggers():
    """
    Configure loggers for different modules with specific configurations.
    """
    loggers = {
        'transaction_service': get_logger(name='transaction_service', environment='development'),
        'user_service': get_logger(name='user_service', environment='production'),
        'authentication': get_logger(name='authentication', environment='testing')
    }
    return loggers

# Optional: Exception hook for unhandled exceptions
def setup_exception_logging():
    """
    Sets up global exception logging.
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        logger = get_logger(name='global_exception')
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    import sys
    sys.excepthook = exception_handler