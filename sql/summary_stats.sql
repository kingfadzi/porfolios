-- 1. Dataset Summary: Record Counts and Completeness
SELECT 
    COUNT(*) AS total_records,
    COUNT(repo_id) AS valid_repo_ids,
    COUNT(DISTINCT main_language) AS unique_languages,
    COUNT(*) FILTER (WHERE total_code IS NULL) AS missing_code_metrics,
    COUNT(*) FILTER (WHERE total_trivy_vulns IS NULL) AS missing_vulnerability_metrics,
    COUNT(*) FILTER (WHERE avg_ccn IS NULL) AS missing_complexity_metrics,
    COUNT(*) FILTER (WHERE iac_dockerfile = 1) AS dockerfile_repos,
    COUNT(*) FILTER (WHERE iac_kubernetes = 1) AS kubernetes_repos
FROM combined_repo_metrics;

-- 2. Key Metric Averages and Distributions
SELECT 
    AVG(total_code) AS avg_total_code,
    MIN(total_code) AS min_total_code,
    MAX(total_code) AS max_total_code,
    STDDEV(total_code) AS stddev_total_code,
    AVG(avg_ccn) AS avg_avg_ccn,
    MIN(avg_ccn) AS min_avg_ccn,
    MAX(avg_ccn) AS max_avg_ccn,
    AVG(total_trivy_vulns) AS avg_total_vulnerabilities,
    MAX(total_trivy_vulns) AS max_total_vulnerabilities,
    COUNT(*) FILTER (WHERE total_trivy_vulns = 0) AS no_vulnerabilities_count
FROM combined_repo_metrics;

-- 3. Language Distribution
SELECT 
    main_language, 
    COUNT(*) AS repo_count,
    AVG(total_code) AS avg_total_code_per_language,
    AVG(total_trivy_vulns) AS avg_vulnerabilities_per_language
FROM combined_repo_metrics
GROUP BY main_language
ORDER BY repo_count DESC;

-- 4. Repositories with High Complexity or Risk
SELECT 
    repo_id,
    total_code,
    avg_ccn,
    total_trivy_vulns,
    language_count,
    main_language
FROM combined_repo_metrics
WHERE 
    avg_ccn > (SELECT AVG(avg_ccn) + 2 * STDDEV(avg_ccn) FROM combined_repo_metrics)
    OR total_trivy_vulns > (SELECT AVG(total_trivy_vulns) + 2 * STDDEV(total_trivy_vulns) FROM combined_repo_metrics)
ORDER BY total_trivy_vulns DESC;

-- 5. Infrastructure-as-Code (IaC) Usage
SELECT 
    COUNT(*) AS total_repos,
    COUNT(*) FILTER (WHERE iac_dockerfile = 1) AS dockerfile_repos,
    COUNT(*) FILTER (WHERE iac_kubernetes = 1) AS kubernetes_repos,
    COUNT(*) FILTER (WHERE iac_terraform = 1) AS terraform_repos,
    COUNT(*) FILTER (WHERE iac_github_actions = 1) AS github_actions_repos
FROM combined_repo_metrics;

-- 6. Technical Debt and Readiness
SELECT 
    repo_id,
    total_code,
    avg_ccn,
    total_trivy_vulns,
    language_count,
    main_language,
    (0.4 * total_code + 0.4 * avg_ccn + 0.2 * total_trivy_vulns) AS technical_debt_score
FROM combined_repo_metrics
ORDER BY technical_debt_score DESC
LIMIT 10;

-- 7. Repository Age and Activity
SELECT 
    repo_id,
    repo_age_days,
    total_commits,
    last_commit_date,
    activity_status,
    CASE 
        WHEN repo_age_days > 1000 THEN 'Legacy'
        WHEN total_commits < 10 THEN 'Inactive'
        ELSE 'Active'
    END AS repo_category
FROM combined_repo_metrics
ORDER BY repo_age_days DESC;

-- 8. Summary of Key Fields
SELECT 
    COUNT(DISTINCT repo_id) AS total_repos,
    AVG(total_code) AS avg_code,
    AVG(avg_ccn) AS avg_complexity,
    AVG(total_trivy_vulns) AS avg_vulnerabilities,
    AVG(language_count) AS avg_languages,
    COUNT(*) FILTER (WHERE main_language = 'Java') AS java_repos,
    COUNT(*) FILTER (WHERE main_language = 'Python') AS python_repos,
    COUNT(*) FILTER (WHERE main_language = 'Go') AS go_repos
FROM combined_repo_metrics;