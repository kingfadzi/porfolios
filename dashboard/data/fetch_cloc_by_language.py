import pandas as pd
from sqlalchemy import text
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

def fetch_cloc_by_language(filters=None):
    @cache.memoize()
    def query_data(condition_string, param_dict):
        base_query = """
            SELECT 
                main_language,
                SUM(total_blank) AS blank_lines,
                SUM(total_comment) AS comment_lines,
                SUM(total_lines_of_code) AS total_lines_of_code,
                SUM(source_code_file_count) AS source_code_file_count
            FROM combined_repo_metrics
            WHERE main_language != 'SUM'
        """
        if condition_string:
            base_query += f" AND {condition_string}"

        base_query += """
            GROUP BY main_language
            ORDER BY total_lines_of_code DESC
            LIMIT 20
        """

        stmt = text(base_query)
        df = pd.read_sql(stmt, engine, params=param_dict)

        # Ensure all numeric columns are integers
        numeric_columns = ["blank_lines", "comment_lines", "total_lines_of_code", "source_code_file_count"]
        for column in numeric_columns:
            if column in df.columns:
                df[column] = df[column].apply(
                    lambda x: int(x) if pd.notnull(x) else None
                )

        return df

    condition_string, param_dict = build_filter_conditions(filters)
    return query_data(condition_string, param_dict)
