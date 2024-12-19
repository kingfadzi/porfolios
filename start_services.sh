#!/bin/bash

# Ensure PostgreSQL data directory exists and is owned by postgres
chown -R postgres:postgres /var/lib/pgsql

# Start PostgreSQL as the postgres user
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/lib/pgsql/data/logfile start"

# Wait for PostgreSQL to fully start
sleep 5

# Check if the Airflow database exists and create it if not
su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='airflow'\"" | grep -q 1 || \
    su - postgres -c "psql -c 'CREATE DATABASE airflow;'"

# Initialize Airflow database (idempotent)
airflow db init

# Start Airflow webserver and scheduler
airflow webserver --port 8088 &
airflow scheduler
