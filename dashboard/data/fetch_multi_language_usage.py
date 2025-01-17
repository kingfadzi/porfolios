from sqlalchemy import text
import pandas as pd
from data.cache_instance import cache
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

def fetch_multi_language_usage(filters=None):
    @cache.memoize()
    def query_data(condition_string, param_dict):
        sql = """
        SELECT
            CASE
                WHEN language_count = 1 THEN '1'
                WHEN language_count BETWEEN 2 AND 5 THEN '2-5'
                WHEN language_count BETWEEN 6 AND 10 THEN '6-10'
                ELSE '10+'
            END AS language_bucket,
            COUNT(DISTINCT repo_id) AS repo_count
        FROM combined_repo_metrics
        """
        if condition_string:
            sql += f" WHERE {condition_string}"
        sql += """
        GROUP BY language_bucket
        ORDER BY repo_count DESC
        """

        stmt = text(sql)
        return pd.read_sql(stmt, engine, params=param_dict)

    condition_string, param_dict = build_filter_conditions(filters)
    return query_data(condition_string, param_dict)