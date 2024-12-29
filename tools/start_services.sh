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

# Wait for PostgreSQL to fully start
sleep 5

# Check if the Airflow database exists and create it if not
su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='airflow'\"" | grep -q 1 || {
    su - postgres -c "psql -c 'CREATE DATABASE airflow;'"
    echo "Initializing Airflow database..."
    airflow db init

    # Set PostgreSQL password and add Airflow admin user
    echo "Setting PostgreSQL password and creating Airflow admin user..."
    su - postgres -c "psql -d airflow -c \"ALTER USER postgres WITH PASSWORD 'postgres';\""
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password password
}

# Start Airflow webserver and scheduler
rm -f /root/airflow/airflow-webserver.pid
airflow webserver --port 8080 &
airflow scheduler
