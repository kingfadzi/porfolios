import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_trivy_vulnerabilities(filters=None):
    @cache.memoize()
    def query_data(filter_conditions):
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

    filter_conditions = build_filter_conditions(filters)
    return query_data(filter_conditions)
