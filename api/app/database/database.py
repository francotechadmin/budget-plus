import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Cloud SQL Python Connector
# Set environment variables
ENV = os.getenv("ENV", "development")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_DBNAME = os.getenv("PG_DBNAME", "postgres")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "mysecretpassword")
PG_PORT = os.getenv("PG_PORT", "5432")

# Create the database URL
if ENV == "production":
    # Production environment
    DB_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"
    logger.debug(f"Using production database URL: {DB_URL}")
else:
    # Development environment
    DB_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"
    logger.debug(f"Using development database URL: {DB_URL}")

# Create the SQLAlchemy engine
try:
    engine: Engine = create_engine(DB_URL, echo=True)
    logger.debug("Database engine created successfully.")
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

# create SQLAlchemy ORM session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
