#!/bin/bash
set -e

# Check if migrations should be run (can be controlled via env var)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running migrations..."
    # Don't create a new revision every time, just upgrade to latest
    alembic upgrade head
else
    echo "Skipping migrations as RUN_MIGRATIONS is not set to true"
fi

# Execute the container's main command (passed as CMD in the Dockerfile)
exec "$@"
