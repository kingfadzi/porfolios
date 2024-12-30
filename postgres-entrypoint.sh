#!/bin/bash
set -e

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if postgres is running
is_postgres_running() {
    su - postgres -c "pg_isready" > /dev/null 2>&1
}

log "Starting PostgreSQL entrypoint script"

# 1. Make sure the data directory belongs to postgres
log "Fixing ownership of /var/lib/pgsql..."
chown -R postgres:postgres /var/lib/pgsql
chmod 700 /var/lib/pgsql/data

# 2. Initialize the DB if needed
if [ ! -f /var/lib/pgsql/data/PG_VERSION ]; then
    log "Initializing PostgreSQL database..."
    su - postgres -c "initdb -D /var/lib/pgsql/data" || { log "Database initialization failed"; exit 1; }

    # Configure external connections
    echo "host all all 0.0.0.0/0 md5" >> /var/lib/pgsql/data/pg_hba.conf
    echo "listen_addresses = '*'" >> /var/lib/pgsql/data/postgresql.conf
    log "PostgreSQL database initialized and configured for external connections."
else
    log "PostgreSQL database already initialized."
fi

# 3. Start PostgreSQL
log "Attempting to start PostgreSQL..."
if [ -z "$1" ]; then
    su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l logfile start" || { log "Failed to start PostgreSQL"; exit 1; }

    # Wait for PostgreSQL to start
    for i in {1..30}; do
        if is_postgres_running; then
            log "PostgreSQL started successfully."
            break
        fi
        log "Waiting for PostgreSQL to start... (attempt $i/30)"
        sleep 1
    done

    if ! is_postgres_running; then
        log "PostgreSQL failed to start after 30 seconds."
        exit 1
    fi

    # Keep the container running
    log "PostgreSQL is running. Container will now sleep infinity."
    exec sleep infinity
else
    log "Executing custom command: $*"
    exec su - postgres -c "$*"
fi
