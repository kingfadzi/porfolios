from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
import pandas as pd

def fetch_cloc_by_language(filters=None):
    """
    Fetch CLOC metrics grouped by main_language, limited to the top 20 languages by total lines of code.
    Excludes rows where main_language='SUM'.
    """
    # Build additional filter conditions based on provided filters
    filter_conditions = build_filter_conditions(filters)

    # Define the SQL query with updated table and column names
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

    # Append additional filter conditions if any
    if filter_conditions:
        query += f" AND {filter_conditions}"

    # Continue building the query with grouping, ordering, and limiting
    query += """
    GROUP BY main_language
    ORDER BY total_lines_of_code DESC
    LIMIT 20
    """

    # Execute the query and return the results as a pandas DataFrame
    df = pd.read_sql(query, engine)

    # Debugging: Print columns to verify
    print("Columns fetched:", df.columns.tolist())
    print(df.head())

    return df
