from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
import pandas as pd

def fetch_contributors_commits_size(filters=None):
    """
    Fetch data for contributors, commits, repository size, and clone_url_ssh as repo_url.
    """
    filter_conditions = build_filter_conditions(filters)

    query = """
    SELECT 
        clone_url_ssh AS repo_url,  -- Alias clone_url_ssh as repo_url
        number_of_contributors AS contractors,
        total_commits AS commits,
        repo_size_bytes AS repo_size
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"

    return pd.read_sql(query, engine)