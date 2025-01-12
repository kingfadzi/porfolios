from sqlalchemy import create_engine
import pandas as pd

def load_data():
    engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")
    query = "SELECT * FROM combined_repo_metrics"
    return pd.read_sql(query, engine)