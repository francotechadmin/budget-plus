#!/bin/bash
set -e

# Run Alembic migrations
echo "Running migrations..."
alembic stamp head
alembic revision --autogenerate -m "migration"
alembic upgrade head

# Execute the container’s main command (passed as CMD in the Dockerfile)
exec "$@"
