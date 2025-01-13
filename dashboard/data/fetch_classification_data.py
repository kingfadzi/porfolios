import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

def fetch_classification_data(filters=None):
    filter_conditions = build_filter_conditions(filters)
    query = """
    SELECT classification_label, COUNT(*) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY classification_label"
    return pd.read_sql(query, engine)