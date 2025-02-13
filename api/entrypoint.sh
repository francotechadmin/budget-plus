#!/bin/bash
set -e

# Run Alembic migrations
echo "Running migrations..."
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Execute the container’s main command (passed as CMD in the Dockerfile)
exec "$@"
