#!/bin/bash
set -e

# Initialize the database if PG_VERSION does not exist
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."
    su postgres -c "initdb -D \"$PGDATA\""

    echo "Configuring PostgreSQL..."
    su postgres -c "echo \"listen_addresses = '*'\" >> \"$PGDATA/postgresql.conf\""
    su postgres -c "echo \"host all all 0.0.0.0/0 md5\" >> \"$PGDATA/pg_hba.conf\""

    echo "Starting PostgreSQL temporarily to create user and database..."
    su postgres -c "pg_ctl -D \"$PGDATA\" -o \"-k /tmp\" -w start"

    # Wait until PostgreSQL is ready to accept connections
    until su postgres -c "psql --host=127.0.0.1 --username=postgres -c '\q'" 2>/dev/null; do
        echo "Waiting for PostgreSQL to start..."
        sleep 1
    done

    # Create user if it doesn't exist
    echo "Creating user 'postgres' if it does not exist..."
    su postgres -c "psql --host=127.0.0.1 --username=postgres -tc \"SELECT 1 FROM pg_roles WHERE rolname = 'postgres'\" | grep -q 1 || psql --host=127.0.0.1 --username=postgres -c \"ALTER ROLE postgres WITH SUPERUSER LOGIN PASSWORD 'postgres';\""

    # Create database if it doesn't exist
    echo "Creating database 'airflow' if it does not exist..."
    su postgres -c "psql --host=127.0.0.1 --username=postgres -tc \"SELECT 1 FROM pg_database WHERE datname = 'airflow'\" | grep -q 1 || psql --host=127.0.0.1 --username=postgres -c \"CREATE DATABASE airflow WITH OWNER postgres;\""

    echo "Stopping temporary PostgreSQL..."
    su postgres -c "pg_ctl -D \"$PGDATA\" -m fast -w stop"

    echo "Database initialization complete."
fi

# Start PostgreSQL in the foreground as 'postgres' user
exec su postgres -c "postgres -D \"$PGDATA\" -k /tmp"
