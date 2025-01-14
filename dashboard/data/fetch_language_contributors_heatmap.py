from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
import pandas as pd

def fetch_language_contributors_heatmap(filters=None):
    filter_conditions = build_filter_conditions(filters)

    query = f"""
    SELECT
        main_language,
        CASE
            WHEN number_of_contributors BETWEEN 0 AND 1 THEN '0-1'
            WHEN number_of_contributors BETWEEN 2 AND 5 THEN '2-5'
            WHEN number_of_contributors BETWEEN 6 AND 10 THEN '6-10'
            WHEN number_of_contributors BETWEEN 11 AND 20 THEN '11-20'
            WHEN number_of_contributors BETWEEN 21 AND 50 THEN '21-50'
            WHEN number_of_contributors BETWEEN 51 AND 100 THEN '51-100'
            WHEN number_of_contributors BETWEEN 101 AND 500 THEN '101-500'
            ELSE '500+'
        END AS contributor_bucket,
        COUNT(DISTINCT repo_id) AS repo_count
    FROM combined_repo_metrics
    WHERE main_language != 'SUM'
    """
    if filter_conditions:
        query += f" AND {filter_conditions}"

    query += """
    GROUP BY main_language, contributor_bucket
    """

    return pd.read_sql(query, engine)
