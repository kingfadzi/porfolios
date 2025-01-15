import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_cloc_by_language(filters=None):
    @cache.memoize()
    def query_data(filter_conditions):
        query = """
        SELECT 
            main_language,
            SUM(total_blank) AS blank_lines,
            SUM(total_comment) AS comment_lines,
            SUM(total_lines_of_code) AS total_lines_of_code,
            SUM(source_code_file_count) AS source_code_file_count
        FROM combined_repo_metrics
        WHERE main_language != 'SUM'
        """
        if filter_conditions:
            query += f" AND {filter_conditions}"
        query += """
        GROUP BY main_language
        ORDER BY total_lines_of_code DESC
        LIMIT 20
        """
        return pd.read_sql(query, engine)

    filter_conditions = build_filter_conditions(filters)
    return query_data(filter_conditions)
