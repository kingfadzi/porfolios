-- =============================================================================
-- 1) Overall IaC Adoption
-- Pie or Doughnut Chart: "Has IaC" vs. "No IaC"
-- =============================================================================
SELECT
  CASE
    WHEN (
      iac_ansible
      + iac_terraform
      + iac_kubernetes
      + iac_dockerfile
      + iac_secrets
      + iac_openapi
      + iac_cloudformation
      + iac_azure_pipelines
      + iac_bitbucket_pipelines
      + iac_circleci_pipelines
      + iac_github_actions
      + iac_gitlab_ci
      + iac_terraform_plan
    ) > 0 THEN 'Has IaC'
    ELSE 'No IaC'
  END AS iac_status,
  COUNT(*) AS repo_count
FROM combined_repo_metrics
GROUP BY 1
ORDER BY 2 DESC;


-- =============================================================================
-- 2) Tool-by-Tool Usage
-- Bar Chart: Compare usage counts of each IaC tool
-- =============================================================================
SELECT
    CASE
        WHEN iac_ansible > 0 THEN 'Ansible'
        WHEN iac_terraform > 0 THEN 'Terraform'
        WHEN iac_kubernetes > 0 THEN 'Kubernetes'
        WHEN iac_dockerfile > 0 THEN 'Dockerfile'
        WHEN iac_secrets > 0 THEN 'Secrets'
        WHEN iac_openapi > 0 THEN 'OpenAPI'
        WHEN iac_cloudformation > 0 THEN 'CloudFormation'
        WHEN iac_azure_pipelines > 0 THEN 'Azure Pipelines'
        WHEN iac_bitbucket_pipelines > 0 THEN 'Bitbucket Pipelines'
        WHEN iac_circleci_pipelines > 0 THEN 'CircleCI Pipelines'
        WHEN iac_github_actions > 0 THEN 'GitHub Actions'
        WHEN iac_gitlab_ci > 0 THEN 'GitLab CI'
        WHEN iac_terraform_plan > 0 THEN 'Terraform Plan'
        ELSE 'No IaC'
        END AS iac_tool,
    COUNT(*) AS repo_count
FROM combined_repo_metrics
GROUP BY 1
ORDER BY 2 DESC;


-- =============================================================================
-- 3) Multi-Tool Repos (Distribution)
-- Histogram or Bar Chart: How many IaC tools each repo uses, aggregated
-- =============================================================================
SELECT
  (
    iac_ansible
    + iac_terraform
    + iac_kubernetes
    + iac_dockerfile
    + iac_secrets
    + iac_openapi
    + iac_cloudformation
    + iac_azure_pipelines
    + iac_bitbucket_pipelines
    + iac_circleci_pipelines
    + iac_github_actions
    + iac_gitlab_ci
    + iac_terraform_plan
  ) AS total_iac_tools,
  COUNT(*) AS repo_count
FROM combined_repo_metrics
GROUP BY 1
ORDER BY 1;


-- =============================================================================
-- 4) IaC Gaps
-- List or Bar Chart: Highlight repos lacking IaC
-- =============================================================================
SELECT
  repo_id,
  main_language,
  classification_label,
  total_lines_of_code AS loc,
  (
    iac_ansible
    + iac_terraform
    + iac_kubernetes
    + iac_dockerfile
    + iac_secrets
    + iac_openapi
    + iac_cloudformation
    + iac_azure_pipelines
    + iac_bitbucket_pipelines
    + iac_circleci_pipelines
    + iac_github_actions
    + iac_gitlab_ci
    + iac_terraform_plan
  ) AS total_iac_tools
FROM combined_repo_metrics
WHERE iac_no_checks = 1
   OR (
       iac_ansible
       + iac_terraform
       + iac_kubernetes
       + iac_dockerfile
       + iac_secrets
       + iac_openapi
       + iac_cloudformation
       + iac_azure_pipelines
       + iac_bitbucket_pipelines
       + iac_circleci_pipelines
       + iac_github_actions
       + iac_gitlab_ci
       + iac_terraform_plan
     ) = 0
ORDER BY repo_id;


-- =============================================================================
-- 5) IaC vs. Repo Classification
-- Grouped Bar or Small Multiple: Compare IaC usage by classification_label
-- =============================================================================
SELECT
  classification_label,
  CASE
    WHEN (
      iac_ansible
      + iac_terraform
      + iac_kubernetes
      + iac_dockerfile
      + iac_secrets
      + iac_openapi
      + iac_cloudformation
      + iac_azure_pipelines
      + iac_bitbucket_pipelines
      + iac_circleci_pipelines
      + iac_github_actions
      + iac_gitlab_ci
      + iac_terraform_plan
    ) > 0 THEN 'Has IaC'
    ELSE 'No IaC'
  END AS iac_status,
  COUNT(*) AS repo_count
FROM combined_repo_metrics
GROUP BY 1, 2
ORDER BY 1, 2;
