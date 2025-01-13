from sqlalchemy import create_engine

# Centralized database connection string
DB_CONNECTION_STRING = "postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage"

# Create the engine only once
engine = create_engine(DB_CONNECTION_STRING)