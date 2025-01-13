from sqlalchemy import create_engine
import pandas as pd
from data.build_filter_conditions import build_filter_conditions

engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")

def fetch_active_inactive_data(filters=None):
    filter_conditions = build_filter_conditions(filters)
    query = """
    SELECT activity_status, COUNT(*) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY activity_status"
    return pd.read_sql(query, engine)