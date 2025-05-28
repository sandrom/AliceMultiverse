#!/bin/bash
# Docker entrypoint script for AliceMultiverse services
# Ensures database migrations are run before starting the application

set -e

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."
    until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL is ready!"
}

# Extract database connection details from DATABASE_URL
if [ ! -z "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: postgresql://user:password@host:port/database
    export POSTGRES_USER=$(echo $DATABASE_URL | sed -E 's|postgresql://([^:]+):.*|\1|')
    export POSTGRES_PASSWORD=$(echo $DATABASE_URL | sed -E 's|postgresql://[^:]+:([^@]+)@.*|\1|')
    export POSTGRES_HOST=$(echo $DATABASE_URL | sed -E 's|postgresql://[^@]+@([^:]+):.*|\1|')
    export POSTGRES_PORT=$(echo $DATABASE_URL | sed -E 's|postgresql://[^@]+@[^:]+:([^/]+)/.*|\1|')
    export POSTGRES_DB=$(echo $DATABASE_URL | sed -E 's|postgresql://[^/]+/(.+)|\1|')
fi

# Only run migrations if DATABASE_URL is set
if [ ! -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL is set, running migrations..."
    
    # Wait for database to be ready
    wait_for_postgres
    
    # Run migrations
    echo "Running database migrations..."
    alembic upgrade head
    
    if [ $? -eq 0 ]; then
        echo "Migrations completed successfully!"
    else
        echo "Migration failed! Exiting..."
        exit 1
    fi
else
    echo "DATABASE_URL not set, skipping migrations"
fi

# Execute the main command
echo "Starting application..."
exec "$@"