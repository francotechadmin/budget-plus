import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import engine_from_config
from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from app.main import Base # Import your Base model

# Logging configuration
from app.utils.logger import get_logger
# Configure logging
logger = get_logger(__name__)
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the models' MetaData object for 'autogenerate' support.
target_metadata = Base.metadata

# Initialize Cloud SQL Python Connector
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_DBNAME = os.getenv("PG_DBNAME", "postgres")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "mysecretpassword")
PG_PORT = os.getenv("PG_PORT", "5432")

logger.debug(f"Connecting to database {PG_DBNAME} at {PG_HOST}")

config.set_main_option(
    "sqlalchemy.url",
    f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"
)


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
    logger.info("Running migrations online")
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))

    def process_revision_directives(context, revision, directives):
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes detected in the database schema, skipping migration.")

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives
        )

        with context.begin_transaction():
            context.run_migrations() 


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
