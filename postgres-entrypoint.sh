#!/bin/bash
set -e

# 1. Make sure the data directory belongs to postgres
echo "Fixing ownership of /var/lib/pgsql..."
chown -R postgres:postgres /var/lib/pgsql
chmod 700 /var/lib/pgsql/data

# 2. Initialize the DB if needed
if [ ! -f /var/lib/pgsql/data/PG_VERSION ]; then
    echo "Initializing PostgreSQL database..."
    su - postgres -c "initdb -D /var/lib/pgsql/data"

    # Configure external connections
    echo "host all all 0.0.0.0/0 md5" >> /var/lib/pgsql/data/pg_hba.conf
    echo "listen_addresses = '*'" >> /var/lib/pgsql/data/postgresql.conf
    echo "PostgreSQL database initialized."
else
    echo "PostgreSQL database already initialized."
fi

# 3. Finally, run Postgres as the postgres user
echo "Starting PostgreSQL..."
if [ "$1" = "" ]; then
    exec su - postgres -c "postgres -D /var/lib/pgsql/data"
else
    exec su - postgres -c "$*"
fi

