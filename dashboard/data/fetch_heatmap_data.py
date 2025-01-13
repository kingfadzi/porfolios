from sqlalchemy import create_engine
import pandas as pd
from data.build_filter_conditions import build_filter_conditions

engine = create_engine("postgresql://postgres@192.168.1.188:5422/gitlab-usage")

def fetch_heatmap_data(filters=None):
    filter_conditions = build_filter_conditions(filters)
    query = """
    SELECT 
        COUNT(*) AS repo_count,
        CASE
            WHEN total_commits BETWEEN 0 AND 50 THEN '0-50'
            WHEN total_commits BETWEEN 51 AND 100 THEN '51-100'
            WHEN total_commits BETWEEN 101 AND 500 THEN '101-500'
            WHEN total_commits BETWEEN 501 AND 1000 THEN '501-1000'
            WHEN total_commits BETWEEN 1001 AND 5000 THEN '1001-5000'
            ELSE '5001+'
        END AS commit_bucket,
        CASE
            WHEN number_of_contributors BETWEEN 0 AND 1 THEN '0-1'
            WHEN number_of_contributors BETWEEN 2 AND 5 THEN '2-5'
            WHEN number_of_contributors BETWEEN 6 AND 10 THEN '6-10'
            WHEN number_of_contributors BETWEEN 11 AND 20 THEN '11-20'
            WHEN number_of_contributors BETWEEN 21 AND 50 THEN '21-50'
            ELSE '51+'
        END AS contributor_bucket
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY commit_bucket, contributor_bucket"
    return pd.read_sql(query, engine)