from sqlalchemy import text
import pandas as pd
from data.cache_instance import cache
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

def fetch_active_inactive_data(filters=None):
    @cache.memoize()
    def query_data(condition_string, param_dict):
        sql = """
        SELECT
            activity_status,
            host_name,
            COUNT(*) AS repo_count
        FROM combined_repo_metrics
        """
        if condition_string:
            sql += f" WHERE {condition_string}"
        sql += " GROUP BY activity_status, host_name"

        stmt = text(sql)
        return pd.read_sql(stmt, engine, params=param_dict)

    # Build both the condition string and parameter dictionary
    condition_string, param_dict = build_filter_conditions(filters)
    return query_data(condition_string, param_dict)
