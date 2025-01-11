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
SELECT 'Ansible'               AS iac_tool, SUM(iac_ansible)               AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'Terraform'             AS iac_tool, SUM(iac_terraform)             AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'Kubernetes'            AS iac_tool, SUM(iac_kubernetes)            AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'Dockerfile'            AS iac_tool, SUM(iac_dockerfile)            AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'Secrets'               AS iac_tool, SUM(iac_secrets)               AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'OpenAPI'               AS iac_tool, SUM(iac_openapi)               AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'CloudFormation'        AS iac_tool, SUM(iac_cloudformation)        AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'Azure Pipelines'       AS iac_tool, SUM(iac_azure_pipelines)       AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'Bitbucket Pipelines'   AS iac_tool, SUM(iac_bitbucket_pipelines)   AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'CircleCI Pipelines'    AS iac_tool, SUM(iac_circleci_pipelines)    AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'GitHub Actions'        AS iac_tool, SUM(iac_github_actions)        AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'GitLab CI'             AS iac_tool, SUM(iac_gitlab_ci)             AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'Terraform Plan'        AS iac_tool, SUM(iac_terraform_plan)        AS usage_count FROM combined_repo_metrics
UNION ALL
SELECT 'No Checks'             AS iac_tool, SUM(iac_no_checks)             AS usage_count FROM combined_repo_metrics
;


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