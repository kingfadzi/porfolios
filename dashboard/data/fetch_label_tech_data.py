from sqlalchemy import text
import pandas as pd
from data.cache_instance import cache
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

@cache.memoize()
def fetch_label_tech_data(filters=None, label_key=None):
    def query_data(condition_string, param_dict):
        sql = """
        SELECT
            label_key,
            label_value,
            COUNT(DISTINCT repo_id) AS repo_count
        FROM combined_repo_violations
        """
        if label_key:
            if condition_string:
                sql += f" WHERE {condition_string} AND label_key = :label_key_param"
            else:
                sql += " WHERE label_key = :label_key_param"
            param_dict["label_key_param"] = label_key
        else:
            if condition_string:
                sql += f" WHERE {condition_string}"
        sql += " GROUP BY label_key, label_value"
        stmt = text(sql)
        return pd.read_sql(stmt, engine, params=param_dict)

    condition_string, param_dict = build_filter_conditions(filters)
    
    # Include label_key and filters in the cache key to avoid duplication
    cache_key = (condition_string, frozenset(param_dict.items()), label_key)
    return cache.cached_function(query_data)(*cache_key)