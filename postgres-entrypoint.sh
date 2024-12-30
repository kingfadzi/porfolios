#!/bin/bash

# Ensure PostgreSQL data directory exists and is owned by postgres
chown -R postgres:postgres /var/lib/pgsql/data

# Initialize PostgreSQL if not already initialized
if [ ! -f /var/lib/pgsql/data/postgresql.conf ]; then
    echo "Initializing PostgreSQL database..."
    su - postgres -c "initdb -D /var/lib/pgsql/data"
    echo "host all all 0.0.0.0/0 md5" >> /var/lib/pgsql/data/pg_hba.conf
    echo "listen_addresses='*'" >> /var/lib/pgsql/data/postgresql.conf
fi

# Start PostgreSQL as the postgres user
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/lib/pgsql/data/logfile start"
