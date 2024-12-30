#!/bin/bash

# Ensure the Airflow database connection is correctly configured
if [ -z "$AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" ]; then
    echo "Environment variable AIRFLOW__DATABASE__SQL_ALCHEMY_CONN is not set. Exiting."
    exit 1
fi

# Wait for the PostgreSQL database to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z $(echo $AIRFLOW__DATABASE__SQL_ALCHEMY_CONN | sed -e 's/^.*@//' -e 's/:.*$//') $(echo $AIRFLOW__DATABASE__SQL_ALCHEMY_CONN | sed -e 's/^.*://'); do
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

# Remove any leftover PID files from previous runs
rm -f /root/airflow/airflow-webserver.pid

# Start the Airflow webserver and scheduler
echo "Starting Airflow webserver..."
airflow webserver --port 8080 &

echo "Starting Airflow scheduler..."
airflow scheduler