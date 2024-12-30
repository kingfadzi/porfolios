#!/bin/bash
set -e

# Function to start PostgreSQL
start_postgres() {
    exec "$@"
}

# Check if PGDATA is initialized by looking for PG_VERSION
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA"

    # Configure PostgreSQL to listen on all addresses
    echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"

    # Configure client authentication to allow all hosts with MD5 passwords
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

    # Optionally, create a PostgreSQL user and database if environment variables are set
    if [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
        echo "Creating user '$POSTGRES_USER'..."
        psql --username postgres <<-EOSQL
            CREATE USER "$POSTGRES_USER" WITH SUPERUSER PASSWORD '$POSTGRES_PASSWORD';
EOSQL
    fi

    if [ -n "$POSTGRES_DB" ]; then
        echo "Creating database '$POSTGRES_DB'..."
        psql --username postgres <<-EOSQL
            CREATE DATABASE "$POSTGRES_DB" WITH OWNER "$POSTGRES_USER";
EOSQL
    fi

    echo "Database initialization complete."
fi

# Start PostgreSQL
start_postgres
