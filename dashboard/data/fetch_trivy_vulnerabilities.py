from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
import pandas as pd

def fetch_trivy_vulnerabilities(filters=None):
    """
    Fetch the count of repositories grouped by vulnerability severity, applying filters.
    """
    filter_conditions = build_filter_conditions(filters)

    query = """
    SELECT 
        CASE
            WHEN t.trivy_critical > 0 THEN 'Critical'
            WHEN t.trivy_high > 0 THEN 'High'
            WHEN t.trivy_medium > 0 THEN 'Medium'
            WHEN t.trivy_low > 0 THEN 'Low'
            ELSE 'No Vulnerabilities'
        END AS severity,
        COUNT(DISTINCT repo_id) AS repo_count
    FROM combined_repo_metrics t
    WHERE t.total_trivy_vulns > 0
    """
    if filter_conditions:
        query += f" AND {filter_conditions}"

    query += " GROUP BY severity"

    return pd.read_sql(query, engine)
