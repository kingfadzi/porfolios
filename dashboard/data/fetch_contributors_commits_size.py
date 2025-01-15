import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_contributors_commits_size(filters=None):
    @cache.memoize()
    def query_data(filter_conditions):
        query = """
        SELECT 
            clone_url_ssh AS repo_url,
            number_of_contributors AS contractors,
            total_commits AS commits,
            repo_size_bytes AS repo_size
        FROM combined_repo_metrics
        """
        if filter_conditions:
            query += f" WHERE {filter_conditions}"
        return pd.read_sql(query, engine)

    filter_conditions = build_filter_conditions(filters)
    return query_data(filter_conditions)
