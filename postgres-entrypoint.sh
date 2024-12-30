#!/bin/bash
set -e

# Ensure PostgreSQL data directory exists and is owned by postgres
echo "Ensuring PostgreSQL data directory exists and has correct permissions..."
chown -R postgres:postgres /var/lib/pgsql/data
chmod 700 /var/lib/pgsql/data

# Initialize PostgreSQL if not already initialized
if [ ! -f /var/lib/pgsql/data/PG_VERSION ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D /var/lib/pgsql/data

    # Configure PostgreSQL for external connections
    echo "host all all 0.0.0.0/0 md5" >> /var/lib/pgsql/data/pg_hba.conf
    echo "listen_addresses = '*'" >> /var/lib/pgsql/data/postgresql.conf
    echo "PostgreSQL database initialized."
else
    echo "PostgreSQL database already initialized."
fi

# Start PostgreSQL
echo "Starting PostgreSQL..."
exec postgres -D /var/lib/pgsql/data
