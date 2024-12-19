#!/bin/bash

# Start PostgreSQL
pg_ctl -D /var/lib/pgsql/data -l /var/lib/pgsql/data/logfile start

# Wait for PostgreSQL to fully start
sleep 5

# Initialize Airflow database
airflow db init

# Start Airflow webserver and scheduler
airflow webserver --port 8088 &
airflow scheduler
