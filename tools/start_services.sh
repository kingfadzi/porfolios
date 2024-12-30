#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
exec > >(tee -a "$AIRFLOW_HOME/entrypoint.log") 2>&1
set -x  # Enable debug mode

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

# Initialize the Airflow database
if airflow db check; then
    echo "Airflow database is already initialized."
else
    echo "Initializing Airflow database..."
    airflow db init
fi

# Check if the admin user already exists
if ! airflow users export | grep -q "\"username\": \"$AIRFLOW_ADMIN_USERNAME\""; then
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

# Start the Airflow webserver if enabled
if [ "${START_WEBSERVER:-true}" = "true" ]; then
    echo "Starting Airflow webserver on port ${AIRFLOW_HOST_PORT:-8088}..."
    airflow webserver --port "${AIRFLOW_HOST_PORT:-8088}" &
fi

# Start the Airflow scheduler if enabled
if [ "${START_SCHEDULER:-true}" = "true" ]; then
    echo "Starting Airflow scheduler..."
    airflow scheduler
fi