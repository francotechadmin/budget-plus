import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector
import google.auth
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Cloud SQL Python Connector
# Set environment variables
ENV = os.getenv("ENV", "development")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "your-cloud-sql-connection-name")
PG_DBNAME = os.getenv("PG_DBNAME", "postgres")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "mysecretpassword")
PG_PORT = os.getenv("PG_PORT", "5432")
IAM_USER = os.getenv("IAM_USER", "default")

# helper function to return SQLAlchemy connection pool
def init_connection_pool(connector: Connector) -> Engine:

    if ENV == "development":
        # Python Connector database connection function
        def getconn():
            conn = connector.connect(
                CLOUD_SQL_CONNECTION_NAME, # Cloud SQL Instance Connection Name
                "pg8000",
                user=PG_USER,
                password=PG_PASSWORD,
                db=PG_DBNAME,
                ip_type="public"  # "private" for private IP
            )
            return conn
    else:
        # Python Connector database connection function
        def getconn():
            conn = connector.connect(
                CLOUD_SQL_CONNECTION_NAME, # Cloud SQL Instance Connection Name
                "pg8000",
                iam_user=IAM_USER,
                db=PG_DBNAME,
                enable_iam_auth=True
            )
            return conn

    SQLALCHEMY_DATABASE_URL = "postgresql+pg8000://"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL , creator=getconn
    )
    return engine

# initialize Cloud SQL Python Connector
connector = Connector()

# create connection pool engine
engine = init_connection_pool(connector)

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
