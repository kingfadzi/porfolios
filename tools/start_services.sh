#!/bin/bash

# Ensure required environment variables are set
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_PORT" ] || [ -z "$AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" ]; then
    echo "Environment variables POSTGRES_HOST, POSTGRES_PORT, or AIRFLOW__DATABASE__SQL_ALCHEMY_CONN are not set. Exiting."
    exit 1
fi

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready on $POSTGRES_HOST:$POSTGRES_PORT..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 2
    echo "Waiting..."
done
echo "PostgreSQL is ready."

# Initialize the Airflow database
echo "Initializing Airflow database..."
airflow db init

# Check if the admin user already exists
if ! airflow users list | grep -q admin; then
    # Create an admin user if it doesn't exist
    echo "Creating Airflow admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password password
else
    echo "Admin user already exists. Skipping user creation."
fi

# Remove leftover PID files
rm -f /root/airflow/airflow-webserver.pid

# Start the Airflow webserver and scheduler
echo "Starting Airflow webserver on port 8080..."
airflow webserver --port 8080 &

echo "Starting Airflow scheduler..."
airflow scheduler