import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_active_inactive_data(filters=None):
    @cache.memoize()
    def query_data(filter_conditions):
        query = """
        SELECT 
            activity_status, 
            host_name, 
            COUNT(*) AS repo_count
        FROM combined_repo_metrics
        """
        if filter_conditions:
            query += f" WHERE {filter_conditions}"
        query += " GROUP BY activity_status, host_name"

        return pd.read_sql(query, engine)

    filter_conditions = build_filter_conditions(filters)
    return query_data(filter_conditions)
