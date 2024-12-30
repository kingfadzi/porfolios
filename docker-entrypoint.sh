#!/bin/bash
set -e

# Function to start PostgreSQL temporarily
start_postgres_temp() {
    pg_ctl -D "$PGDATA" -o "-c listen_addresses='localhost' -c logging_collector=off" -w start
}

# Function to stop PostgreSQL temporarily
stop_postgres_temp() {
    pg_ctl -D "$PGDATA" -m fast -w stop
}

# Initialize the database if PG_VERSION does not exist
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA"

    echo "Configuring PostgreSQL..."
    echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

    echo "Starting PostgreSQL temporarily to create user and database..."
    start_postgres_temp

    # Wait until PostgreSQL is ready to accept connections
    until psql --host=localhost --username=postgres -c '\q' 2>/dev/null; do
        echo "Waiting for PostgreSQL to start..."
        sleep 1
    done

    if [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
        echo "Creating user '$POSTGRES_USER'..."
        psql --host=localhost --username=postgres <<-EOSQL
            CREATE USER "$POSTGRES_USER" WITH SUPERUSER PASSWORD '$POSTGRES_PASSWORD';
EOSQL
    fi

    if [ -n "$POSTGRES_DB" ]; then
        echo "Creating database '$POSTGRES_DB'..."
        psql --host=localhost --username=postgres <<-EOSQL
            CREATE DATABASE "$POSTGRES_DB" WITH OWNER "$POSTGRES_USER";
EOSQL
    fi

    echo "Stopping temporary PostgreSQL..."
    stop_postgres_temp

    echo "Database initialization complete."
fi

# Start PostgreSQL in the foreground
exec "$@"
