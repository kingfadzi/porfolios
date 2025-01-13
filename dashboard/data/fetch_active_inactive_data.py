import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

def fetch_active_inactive_data(filters=None):
    """
    Fetch data for the Active vs Inactive chart.
    :param filters: (dict) Filters to apply.
    :return: DataFrame with aggregated data.
    """
    filter_conditions = build_filter_conditions(filters)

    query = """
    SELECT activity_status, COUNT(*) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY activity_status"

    return pd.read_sql(query, engine)