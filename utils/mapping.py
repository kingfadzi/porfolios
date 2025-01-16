import pandas as pd
from sqlalchemy import create_engine

# Database connection
engine = create_engine("postgresql://postgres:postgres@localhost/dbname")

def populate_business_app_mapping(df):
    business_app_df = (
        df[df['mapping_type'] == 'ba']
        .drop_duplicates(subset=['component_id', 'identifier'])
        [['component_id', 'transaction_cycle', 'component_name', 'identifier']]
        .rename(columns={'identifier': 'business_app_identifier'})
    )
    business_app_df.to_sql('business_app_mapping', engine, if_exists='append', index=False, method='multi')


def populate_version_control_mapping(df):
    version_control_df = (
        df[df['mapping_type'] == 'vs']
        .drop_duplicates(subset=['component_id', 'project_key', 'repo_slug'])
        [['component_id', 'project_key', 'repo_slug']]
    )
    version_control_df.to_sql('version_control_mapping', engine, if_exists='append', index=False, method='multi')


def populate_repo_business_mapping(df):
    vs_df = df[df['mapping_type'] == 'vs']
    ba_df = df[df['mapping_type'] == 'ba']

    repo_business_df = (
        vs_df.merge(ba_df, on='component_id', suffixes=('_vs', '_ba'))
        [['component_id', 'project_key', 'repo_slug', 'identifier']]
        .drop_duplicates()
        .rename(columns={'identifier': 'business_app_identifier'})
    )
    repo_business_df.to_sql('repo_business_mapping', engine, if_exists='append', index=False, method='multi')


def main():
    df = pd.read_sql("SELECT * FROM component_mapping", engine)

    populate_business_app_mapping(df)
    populate_version_control_mapping(df)
    populate_repo_business_mapping(df)


if __name__ == "__main__":
    main()
