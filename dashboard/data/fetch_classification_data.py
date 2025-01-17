import pandas as pd
from sqlalchemy import text
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_classification_data(filters=None):
    @cache.memoize()
    def query_data(condition_string, param_dict):
        sql = """
        SELECT classification_label, COUNT(*) AS repo_count
        FROM combined_repo_metrics
        """
        if condition_string:
            sql += f" WHERE {condition_string}"
        sql += " GROUP BY classification_label"

        stmt = text(sql)
        return pd.read_sql(stmt, engine, params=param_dict)

    condition_string, param_dict = build_filter_conditions(filters)
    return query_data(condition_string, param_dict)
