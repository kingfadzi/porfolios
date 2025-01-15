import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_semgrep_findings(filters=None):
    @cache.memoize()
    def query_data(filter_conditions):
        query = """
        SELECT 
            CASE
                WHEN s.cat_best_practice > 0 THEN 'Best Practice'
                WHEN s.cat_compatibility > 0 THEN 'Compatibility'
                WHEN s.cat_correctness > 0 THEN 'Correctness'
                WHEN s.cat_maintainability > 0 THEN 'Maintainability'
                WHEN s.cat_performance > 0 THEN 'Performance'
                WHEN s.cat_portability > 0 THEN 'Portability'
                WHEN s.cat_security > 0 THEN 'Security'
                ELSE 'No Findings'
            END AS category,
            COUNT(DISTINCT repo_id) AS repo_count
        FROM combined_repo_metrics s
        WHERE s.total_semgrep_findings > 0
        """
        if filter_conditions:
            query += f" AND {filter_conditions}"
        query += " GROUP BY category"
        return pd.read_sql(query, engine)

    filter_conditions = build_filter_conditions(filters)
    return query_data(filter_conditions)
