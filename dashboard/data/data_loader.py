from sqlalchemy import create_engine
import pandas as pd

# Initialize database connection
engine = create_engine("postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage")

def fetch_dropdown_options():
    """
    Fetch unique values for dropdown fields.
    :return: Dictionary of options for dropdowns.
    """
    query = """
    SELECT DISTINCT 
        host_name, 
        main_language, 
        classification_label, 
        activity_status
    FROM combined_repo_metrics
    """
    df = pd.read_sql(query, engine)

    return {
        "host_names": df["host_name"].dropna().unique().tolist(),
        "languages": df["main_language"].dropna().unique().tolist(),
        "classification_labels": df["classification_label"].dropna().unique().tolist(),
        "activity_statuses": df["activity_status"].dropna().unique().tolist(),
    }

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