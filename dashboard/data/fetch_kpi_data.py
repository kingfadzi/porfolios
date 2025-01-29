import pandas as pd
from sqlalchemy import text
from data.cache_instance import cache
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

def human_readable_size(size_in_bytes):
    if size_in_bytes is None:
        size_in_bytes = 0
    if size_in_bytes < 1024:
        return f"{size_in_bytes:.2f} B"
    elif size_in_bytes < 1024**2:
        return f"{(size_in_bytes / 1024):.2f} KB"
    elif size_in_bytes < 1024**3:
        return f"{(size_in_bytes / (1024**2)):.2f} MB"
    else:
        return f"{(size_in_bytes / (1024**3)):.2f} GB"

@cache.memoize()
def fetch_kpi_data(filters=None):
    condition_string, param_dict = build_filter_conditions(filters)
    sql = """
    SELECT
        COUNT(*)::bigint AS total_repos,
        AVG(total_commits) AS avg_commits,
        AVG(number_of_contributors) AS avg_contributors,
        AVG(total_lines_of_code) AS avg_loc,
        AVG(total_cyclomatic_complexity) AS avg_ccn,
        AVG(repo_size_bytes) AS avg_repo_size
    FROM combined_repo_metrics_api
    """
    if condition_string:
        sql += f" WHERE {condition_string}"
    df = pd.read_sql(text(sql), engine, params=param_dict)
    if df.empty:
        return {
            "total_repos": "0",
            "avg_commits": "0",
            "avg_contributors": "0",
            "avg_loc": "0",
            "avg_ccn": "0",
            "avg_repo_size": "0.00 B"
        }
    row = df.iloc[0]
    total_repos = f"{(row['total_repos'] or 0):,.0f}"
    avg_commits = f"{(row['avg_commits'] or 0):,.0f}"
    avg_contributors = f"{(row['avg_contributors'] or 0):,.0f}"
    avg_loc = f"{(row['avg_loc'] or 0):,.0f}"
    avg_ccn = f"{(row['avg_ccn'] or 0):,.0f}"
    avg_repo_size_str = human_readable_size(row['avg_repo_size'])
    return {
        "total_repos": total_repos,
        "avg_commits": avg_commits,
        "avg_contributors": avg_contributors,
        "avg_loc": avg_loc,
        "avg_ccn": avg_ccn,
        "avg_repo_size": avg_repo_size_str,
    }
