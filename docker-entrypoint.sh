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

    if [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
        echo "Creating user '$POSTGRES_USER'..."
        su postgres -c "psql --host=127.0.0.1 --username=postgres <<-EOSQL
            CREATE USER \"$POSTGRES_USER\" WITH SUPERUSER PASSWORD '$POSTGRES_PASSWORD';
EOSQL"
    fi

    if [ -n "$POSTGRES_DB" ]; then
        echo "Creating database '$POSTGRES_DB'..."
        su postgres -c "psql --host=127.0.0.1 --username=postgres <<-EOSQL
            CREATE DATABASE \"$POSTGRES_DB\" WITH OWNER \"$POSTGRES_USER\";
EOSQL"
    fi

    echo "Stopping temporary PostgreSQL..."
    su postgres -c "pg_ctl -D \"$PGDATA\" -m fast -w stop"

    echo "Database initialization complete."
fi

# Start PostgreSQL in the foreground as 'postgres' user
exec su postgres -c "$@"
