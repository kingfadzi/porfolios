#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Debugging: Log all environment variables
echo "DEBUG: POSTGRES_HOST=${POSTGRES_HOST}"
echo "DEBUG: POSTGRES_PORT=${POSTGRES_PORT}"
echo "DEBUG: AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}"

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    echo "Waiting for $host:$port to be available..."
    for i in {1..30}; do
        if nc -z "$host" "$port"; then
            echo "$host:$port is available."
            return 0
        fi
        sleep 2
        echo "Retrying ($i/30)..."
    done
    echo "Error: $host:$port is not reachable after 30 retries."
    exit 1
}

# Wait for PostgreSQL to be ready
wait_for_service "$POSTGRES_HOST" "$POSTGRES_PORT"

# Initialize the Airflow database if needed
if ! airflow db check; then
    echo "Initializing Airflow database..."
    airflow db init
else
    echo "Airflow database is already initialized."
fi

# Check if the admin user already exists
if ! airflow users list | grep -q "$AIRFLOW_ADMIN_USERNAME"; then
    echo "Creating Airflow admin user..."
    airflow users create \
        --username "$AIRFLOW_ADMIN_USERNAME" \
        --firstname "$AIRFLOW_ADMIN_FIRSTNAME" \
        --lastname "$AIRFLOW_ADMIN_LASTNAME" \
        --role Admin \
        --email "$AIRFLOW_ADMIN_EMAIL" \
        --password "$AIRFLOW_ADMIN_PASSWORD"
else
    echo "Admin user '$AIRFLOW_ADMIN_USERNAME' already exists. Skipping user creation."
fi

# Remove leftover PID files
rm -f "$AIRFLOW_HOME/airflow-webserver.pid"

# Start the Airflow webserver
echo "Starting Airflow webserver on port ${AIRFLOW_HOST_PORT:-8088}..."
airflow webserver --port "${AIRFLOW_HOST_PORT:-8088}" &
echo "Airflow webserver started."

# Start the Airflow scheduler
echo "Starting Airflow scheduler..."
airflow scheduler