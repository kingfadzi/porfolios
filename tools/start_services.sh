#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    echo "Waiting for $host:$port to be available..."
    while ! nc -z "$host" "$port"; do
        sleep 2
        echo "Waiting..."
    done
    echo "$host:$port is available."
}

# Wait for PostgreSQL to be ready
wait_for_service "$POSTGRES_HOST" "$POSTGRES_PORT"

# Initialize the Airflow database
echo "Initializing Airflow database..."
airflow db init

# Check if the admin user already exists
if ! airflow users list | grep -q "$AIRFLOW_ADMIN_USERNAME"; then
    # Create an admin user if it doesn't exist
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

# Start the Airflow webserver in the background on port 8088
echo "Starting Airflow webserver on port ${AIRFLOW_HOST_PORT:-8088}..."
airflow webserver --port "${AIRFLOW_HOST_PORT:-8088}" &

# Start the Airflow scheduler
echo "Starting Airflow scheduler..."
airflow scheduler
