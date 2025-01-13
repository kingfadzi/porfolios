from sqlalchemy import create_engine

# Define the database connection string
DB_CONNECTION_STRING = "postgresql://postgres:your_password@192.168.1.188:5422/gitlab-usage"

# Create the database engine once
engine = create_engine(DB_CONNECTION_STRING)