import os
from logging.config import fileConfig
from alembic import context
from google.cloud.sql.connector import Connector
from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from app.main import Base # Import your Base model

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the models' MetaData object for 'autogenerate' support.
target_metadata = Base.metadata

# Initialize Cloud SQL Python Connector
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "your-cloud-sql-connection-name")
PG_DBNAME = os.getenv("PG_DBNAME", "postgres")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "mysecretpassword")
PG_PORT = os.getenv("PG_PORT", "5433")

config.set_main_option(
    "sqlalchemy.url",
    f"postgresql+pg8000://{PG_USER}:{PG_PASSWORD}@{CLOUD_SQL_CONNECTION_NAME}:{PG_PORT}/{PG_DBNAME}",
)

# helper function to return SQLAlchemy connection pool
def init_connection_pool(connector: Connector) -> Engine:
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

    SQLALCHEMY_DATABASE_URL = "postgresql+pg8000://"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL , creator=getconn
    )
    return engine

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connector = Connector()
    connectable = init_connection_pool(connector)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
