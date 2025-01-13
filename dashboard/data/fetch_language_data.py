import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")

def fetch_language_data(filters=None):
    filter_conditions = build_filter_conditions(filters)
    query = """
    SELECT main_language, COUNT(*) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY main_language"
    return pd.read_sql(query, engine)