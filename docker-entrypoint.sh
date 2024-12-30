#!/bin/bash
set -e

# Function to start PostgreSQL
start_postgres() {
    exec postgres -D "$PGDATA"
}

# Check if PGDATA is empty
if [ -z "$(ls -A "$PGDATA")" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA"

    # Modify postgresql.conf to listen on all addresses
    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"

    # Modify pg_hba.conf to allow connections from all hosts
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

    # Start PostgreSQL temporarily to set up initial database and user
    pg_ctl -D "$PGDATA" -o "-c listen_addresses='localhost'" -w start

    if [ "$POSTGRES_USER" ] && [ "$POSTGRES_PASSWORD" ]; then
        echo "Creating user $POSTGRES_USER..."
        psql --username postgres <<-EOSQL
            CREATE USER "$POSTGRES_USER" WITH SUPERUSER PASSWORD '$POSTGRES_PASSWORD';
EOSQL
    fi

    if [ "$POSTGRES_DB" ]; then
        echo "Creating database $POSTGRES_DB..."
        psql --username postgres <<-EOSQL
            CREATE DATABASE "$POSTGRES_DB" WITH OWNER "$POSTGRES_USER";
EOSQL
    fi

    pg_ctl -D "$PGDATA" -m fast -w stop
fi

# Start PostgreSQL
start_postgres
