import pandas as pd
from sqlalchemy import text
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_contributors_commits_size(filters=None):
    @cache.memoize()
    def query_data(condition_string, param_dict):
        base_query = """
            SELECT 
                clone_url_ssh AS repo_url,
                number_of_contributors AS contractors,
                total_commits AS commits,
                repo_size_bytes AS repo_size
            FROM combined_repo_metrics
        """
        if condition_string:
            base_query += f" WHERE {condition_string}"

        stmt = text(base_query)
        return pd.read_sql(stmt, engine, params=param_dict)

    condition_string, param_dict = build_filter_conditions(filters)
    return query_data(condition_string, param_dict)
