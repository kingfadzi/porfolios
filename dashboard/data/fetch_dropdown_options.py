import pandas as pd
from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions

def fetch_dropdown_options():
    query = """
    SELECT DISTINCT 
        host_name, 
        activity_status, 
        tc, 
        main_language, 
        classification_label
    FROM combined_repo_metrics
    """
    df = pd.read_sql(query, engine)
    return {
        "host_names": sorted(df["host_name"].dropna().unique().tolist()),
        "activity_statuses": sorted(df["activity_status"].dropna().unique().tolist()),
        "tcs": sorted(df["tc"].dropna().unique().tolist()),
        "languages": sorted(df["main_language"].dropna().unique().tolist()),
        "classification_labels": sorted(df["classification_label"].dropna().unique().tolist()),
    }