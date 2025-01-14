from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions_with_alias
import pandas as pd

def fetch_language_contributors_heatmap(filters=None):
    """
    Fetch data for a heatmap of top 20 languages (x-axis) and contributor buckets (y-axis).
    """
    # Build filter conditions with the table alias 'cm'
    filter_conditions = build_filter_conditions_with_alias(filters, alias="cm")

    query = f"""
    WITH top_languages AS (
        SELECT 
            cm.main_language,
            COUNT(DISTINCT cm.repo_id) AS total_repos
        FROM combined_repo_metrics cm
        WHERE cm.main_language != 'SUM'
        GROUP BY cm.main_language
        ORDER BY total_repos DESC
        LIMIT 20
    )
    SELECT 
        cm.main_language AS language,  -- Alias main_language as language
        CASE
            WHEN cm.number_of_contributors BETWEEN 0 AND 1 THEN '0-1'
            WHEN cm.number_of_contributors BETWEEN 2 AND 5 THEN '2-5'
            WHEN cm.number_of_contributors BETWEEN 6 AND 10 THEN '6-10'
            WHEN cm.number_of_contributors BETWEEN 11 AND 20 THEN '11-20'
            WHEN cm.number_of_contributors BETWEEN 21 AND 50 THEN '21-50'
            WHEN cm.number_of_contributors BETWEEN 51 AND 100 THEN '51-100'
            WHEN cm.number_of_contributors BETWEEN 101 AND 500 THEN '101-500'
            ELSE '500+'
        END AS contributor_bucket,
        COUNT(DISTINCT cm.repo_id) AS repo_count
    FROM combined_repo_metrics cm
    INNER JOIN top_languages tl ON cm.main_language = tl.main_language
    """
    if filter_conditions:
        query += f" AND {filter_conditions}"

    query += """
    GROUP BY cm.main_language, contributor_bucket
    """

    return pd.read_sql(query, engine)
