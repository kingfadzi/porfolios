from data.db_connection import engine
from data.build_filter_conditions import build_filter_conditions
import pandas as pd

def fetch_iac_data(filters=None):
    """
    Fetch the count of repositories for each IaC type (excluding 'No IaC'), applying filters.
    """
    filter_conditions = build_filter_conditions(filters)

    query = f"""
    SELECT 
        CASE
            WHEN iac_ansible > 0 THEN 'Ansible'
            WHEN iac_azure_pipelines > 0 THEN 'Azure Pipelines'
            WHEN iac_bitbucket_pipelines > 0 THEN 'Bitbucket Pipelines'
            WHEN iac_circleci_pipelines > 0 THEN 'CircleCI Pipelines'
            WHEN iac_cloudformation > 0 THEN 'CloudFormation'
            WHEN iac_dockerfile > 0 THEN 'Dockerfile'
            WHEN iac_github_actions > 0 THEN 'GitHub Actions'
            WHEN iac_gitlab_ci > 0 THEN 'GitLab CI'
            WHEN iac_kubernetes > 0 THEN 'Kubernetes'
            WHEN iac_no_checks > 0 THEN 'No Checks'
            WHEN iac_openapi > 0 THEN 'OpenAPI'
            WHEN iac_secrets > 0 THEN 'Secrets'
            WHEN iac_terraform > 0 THEN 'Terraform'
            WHEN iac_terraform_plan > 0 THEN 'Terraform Plan'
            ELSE 'No IaC'
        END AS iac_type,
        COUNT(DISTINCT repo_id) AS repo_count
    FROM combined_repo_metrics
    """
    if filter_conditions:
        query += f" WHERE {filter_conditions}"
    query += """
    GROUP BY iac_type
    HAVING iac_type != 'No IaC'
    """

    return pd.read_sql(query, engine)
