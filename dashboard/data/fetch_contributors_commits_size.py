import logging
import pandas as pd
from sqlalchemy import text
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
from data.cache_instance import cache

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def human_readable_age(days):
    if days < 7:
        return f"{days} days"
    elif days < 30:
        return f"{days // 7} weeks"
    elif days < 365:
        return f"{days // 30} months"
    else:
        return f"{days // 365} years"

def deduplicate_comma_separated_values(values):
    if not values:
        return ""
    unique_values = set(values.split(","))
    return ",".join(sorted(unique_values))

def fetch_contributors_commits_size(filters=None):
    @cache.memoize()
    def query_data(condition_string, param_dict):
        base_query = """
            SELECT 
                clone_url_ssh AS repo_url,
                number_of_contributors AS contributors,
                total_commits AS commits,
                repo_size_bytes AS repo_size,
                app_id,
                web_url,
                tc,
                component_id,
                all_languages,
                repo_age_days,
                file_count,
                total_lines_of_code
            FROM combined_repo_metrics
        """
        if condition_string:
            base_query += f" WHERE {condition_string}"

        # Log the query and parameters
        logger.debug("Executing query:")
        logger.debug(base_query)
        logger.debug("With parameters:")
        logger.debug(param_dict)

        stmt = text(base_query)
        df = pd.read_sql(stmt, engine, params=param_dict)

        # Apply transformations
        df["app_id"] = df["app_id"].apply(deduplicate_comma_separated_values)
        df["repo_age_human"] = df["repo_age_days"].apply(human_readable_age)
        df["total_lines_of_code"] = df["total_lines_of_code"].apply(
            lambda x: f"{int(x):,}" if pd.notnull(x) else None
        )
        return df

    condition_string, param_dict = build_filter_conditions(filters)
    return query_data(condition_string, param_dict)
