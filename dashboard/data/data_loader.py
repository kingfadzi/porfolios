from sqlalchemy import create_engine
import pandas as pd

# Initialize database connection
engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")

def build_filter_conditions(filters):
    """
    Build a dynamic SQL WHERE clause based on filter inputs.

    :param filters: (dict) Dictionary of filter fields and their selected values.
    :return: (str) SQL WHERE clause.
    """
    conditions = []
    for field, values in filters.items():
        if values:  # If there are selected values
            formatted_values = ",".join([f"'{value}'" for value in values])
            conditions.append(f"{field} IN ({formatted_values})")

    return " AND ".join(conditions) if conditions else None

def fetch_active_inactive_data(filters=None):
    """
    Fetch data for the Active vs Inactive chart.
    :param filters: (dict) Filters to apply.
    :return: DataFrame with aggregated data.
    """
    filter_conditions = build_filter_conditions(filters)
    
    query = """
    SELECT activity_status, COUNT(*) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY activity_status"

    return pd.read_sql(query, engine)

def fetch_classification_data(filters=None):
    """
    Fetch data for the classification pie chart.
    :param filters: (dict) Filters to apply.
    :return: DataFrame with aggregated data.
    """
    filter_conditions = build_filter_conditions(filters)
    
    query = """
    SELECT classification_label, COUNT(*) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY classification_label"

    return pd.read_sql(query, engine)

def fetch_language_data(filters=None):
    """
    Fetch data for the repositories by language bar chart.
    :param filters: (dict) Filters to apply.
    :return: DataFrame with aggregated data.
    """
    filter_conditions = build_filter_conditions(filters)
    
    query = """
    SELECT main_language, COUNT(*) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += " GROUP BY main_language"

    return pd.read_sql(query, engine)

def fetch_heatmap_data(filters=None):
    """
    Fetch data for the heatmap visualization.
    :param filters: (dict) Filters to apply.
    :return: DataFrame with aggregated data.
    """
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