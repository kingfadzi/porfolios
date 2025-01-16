import pandas as pd
from sqlalchemy import create_engine

# Create SQLAlchemy engine
engine = create_engine("postgresql://postgres:postgres@localhost/dbname")

def populate_business_app_mapping(engine):
    query = """
        SELECT DISTINCT component_id, transaction_cycle, component_name, identifier
        FROM component_mapping
        WHERE mapping_type = 'ba'
    """
    df = pd.read_sql(query, engine)
    df = df.rename(columns={"identifier": "business_app_identifier"})
    df.to_sql("business_app_mapping", engine, if_exists="append", index=False, method="multi")


def populate_version_control_mapping(engine):
    query = """
        SELECT DISTINCT component_id, project_key, repo_slug
        FROM component_mapping
        WHERE mapping_type = 'vs'
    """
    df = pd.read_sql(query, engine)
    df.to_sql("version_control_mapping", engine, if_exists="append", index=False, method="multi")


def populate_repo_business_mapping(engine):
    query_vs = """
        SELECT DISTINCT component_id, project_key, repo_slug
        FROM component_mapping
        WHERE mapping_type = 'vs'
    """
    query_ba = """
        SELECT DISTINCT component_id, identifier
        FROM component_mapping
        WHERE mapping_type = 'ba'
    """
    df_vs = pd.read_sql(query_vs, engine)
    df_ba = pd.read_sql(query_ba, engine)

    merged_df = df_vs.merge(df_ba, on="component_id")
    merged_df = merged_df.rename(columns={"identifier": "business_app_identifier"})
    merged_df.to_sql("repo_business_mapping", engine, if_exists="append", index=False, method="multi")


def main():
    populate_business_app_mapping(engine)
    populate_version_control_mapping(engine)
    populate_repo_business_mapping(engine)


if __name__ == "__main__":
    main()
