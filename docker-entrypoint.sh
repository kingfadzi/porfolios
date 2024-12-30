#!/bin/bash
set -e

# If the database is not initialized (i.e., PG_VERSION is missing),
# then run initdb and configure the basics.
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA"

    # Sample configuration changes
    echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

    # You can optionally start a temporary Postgres to create
    # users/databases:
    # pg_ctl -D "$PGDATA" -o "-c listen_addresses='localhost'" -w start
    #
    # psql --username postgres <<-EOSQL
    #    CREATE USER myuser WITH SUPERUSER PASSWORD 'mypassword';
    #    CREATE DATABASE mydb WITH OWNER myuser;
    # EOSQL
    #
    # pg_ctl -D "$PGDATA" -m fast -w stop
fi

# Exec the final command (usually "postgres -D /var/lib/pgsql/data")
exec "$@"
