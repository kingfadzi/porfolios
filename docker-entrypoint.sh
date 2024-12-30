#!/bin/bash
set -e

# Start PostgreSQL function
start_postgres() {
    exec postgres -D "$PGDATA"
}

# If the data directory is empty, run initdb
if [ -z "$(ls -A "$PGDATA")" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA"

    # Sample config changes (listens on all, allows all inbound)
    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

    # Start Postgres in background to create initial user/database
    pg_ctl -D "$PGDATA" -o "-c listen_addresses='localhost'" -w start

    # If you set POSTGRES_USER/POSTGRES_PASSWORD in `docker run -e`, create that user
    if [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
        echo "Creating user $POSTGRES_USER..."
        psql --username postgres <<-EOSQL
            CREATE USER "$POSTGRES_USER" WITH SUPERUSER PASSWORD '$POSTGRES_PASSWORD';
EOSQL
    fi

    # If you set POSTGRES_DB in `docker run -e`, create that DB
    if [ -n "$POSTGRES_DB" ]; then
        echo "Creating database $POSTGRES_DB..."
        psql --username postgres <<-EOSQL
            CREATE DATABASE "$POSTGRES_DB" WITH OWNER "$POSTGRES_USER";
EOSQL
    fi

    # Stop the temporary Postgres
    pg_ctl -D "$PGDATA" -m fast -w stop
fi

# Finally, start Postgres (foreground)
start_postgres
