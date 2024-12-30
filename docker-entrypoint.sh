#!/bin/bash
set -e

if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL database..."
    initdb -D "$PGDATA"

    # Now create the log folder after initdb is done
    mkdir -p "$PGDATA/log"

    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
fi

exec "$@"
