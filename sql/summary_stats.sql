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

-- 1. Overall Repository Summary (ACTIVE Only)
SELECT
    COUNT(*) AS total_active_repos,
    AVG(repo_size_bytes) AS avg_repo_size,
    AVG(number_of_files) AS avg_number_of_files,
    AVG(number_of_contributors) AS avg_number_of_contributors,
    MAX(last_commit_date) AS most_recent_commit
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 2. Semgrep Coverage (ACTIVE Only)
SELECT
    COUNT(*) AS total_active_repos,
    COUNT(*) FILTER (WHERE total_semgrep_findings > 0) AS active_repos_with_semgrep,
    (COUNT(*) FILTER (WHERE total_semgrep_findings > 0) * 100.0 / COUNT(*)) AS active_semgrep_coverage_percentage
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 3. Distribution of Semgrep Findings (ACTIVE Only)
SELECT
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_semgrep_findings) AS median_findings,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY total_semgrep_findings) AS p90_findings,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_semgrep_findings) AS p99_findings,
    COUNT(*) FILTER (WHERE total_semgrep_findings = 0) AS active_repos_without_findings
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 4. Aggregate Semgrep Findings (ACTIVE Only)
SELECT
    SUM(total_semgrep_findings) AS total_findings,
    SUM(cat_security) AS total_security_findings,
    SUM(cat_correctness) AS total_correctness_findings,
    SUM(cat_maintainability) AS total_maintainability_findings,
    SUM(cat_performance) AS total_performance_findings,
    SUM(cat_portability) AS total_portability_findings,
    SUM(cat_best_practice) AS total_best_practice_findings
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 5. IaC Adoption Summary (ACTIVE Only)
SELECT
    COUNT(*) AS total_active_repos,
    COUNT(*) FILTER (WHERE iac_dockerfile = 1) AS dockerfile_repos,
    COUNT(*) FILTER (WHERE iac_kubernetes = 1) AS kubernetes_repos,
    COUNT(*) FILTER (WHERE iac_terraform = 1) AS terraform_repos,
    COUNT(*) FILTER (WHERE iac_github_actions = 1) AS github_actions_repos,
    COUNT(*) FILTER (WHERE iac_terraform_plan = 1) AS terraform_plan_repos
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 6. High-Risk Repositories (ACTIVE Only)
SELECT
    repo_id,
    total_code,
    avg_ccn,
    total_trivy_vulns,
    total_semgrep_findings,
    number_of_contributors,
    repo_size_bytes,
    total_commits
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND (total_trivy_vulns > 10 OR avg_ccn > 5 OR total_semgrep_findings > 50)
ORDER BY total_trivy_vulns DESC, avg_ccn DESC;

-- 7. File Size and Code Relationships (ACTIVE Only)
SELECT
    repo_id,
    repo_size_bytes,
    number_of_files,
    total_code,
    repo_size_bytes / NULLIF(number_of_files, 1) AS size_per_file,
    total_code / NULLIF(number_of_files, 1) AS code_per_file
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
ORDER BY size_per_file DESC;

-- 8. Commit Activity (ACTIVE Only)
SELECT
    repo_id,
    total_commits,
    number_of_contributors,
    total_commits / NULLIF(number_of_contributors, 1) AS commits_per_contributor,
    last_commit_date
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
ORDER BY total_commits DESC;

-- 9. Repositories Without Semgrep Findings (ACTIVE Only)
SELECT
    repo_id,
    total_code,
    number_of_files,
    number_of_contributors,
    repo_size_bytes,
    last_commit_date
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND total_semgrep_findings = 0
ORDER BY last_commit_date DESC;

-- 10. Correlation Analysis (ACTIVE Only)
SELECT
    CORR(number_of_contributors, total_semgrep_findings) AS contributors_findings_corr,
    CORR(number_of_contributors, total_code) AS contributors_code_corr,
    CORR(total_code, total_semgrep_findings) AS code_findings_corr
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 11. Age of Repositories (ACTIVE Only)
SELECT
    repo_id,
    repo_age_days,
    total_commits,
    total_semgrep_findings,
    last_commit_date,
    CASE
        WHEN repo_age_days > 1000 THEN 'Legacy'
        ELSE 'Modern'
    END AS age_category
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
ORDER BY repo_age_days DESC;

-- 12. Semgrep Findings by Repository Age (ACTIVE Only)
SELECT
    repo_id,
    repo_age_days,
    total_semgrep_findings,
    cat_security,
    cat_correctness,
    total_code
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
ORDER BY repo_age_days DESC, total_semgrep_findings DESC;

-- 13. Aggregate IaC and Semgrep Data (ACTIVE Only)
SELECT
    COUNT(*) AS total_active_repos,
    COUNT(*) FILTER (WHERE iac_dockerfile = 1) AS dockerfile_repos,
    COUNT(*) FILTER (WHERE iac_kubernetes = 1) AS kubernetes_repos,
    COUNT(*) FILTER (WHERE total_semgrep_findings > 0) AS repos_with_semgrep,
    SUM(total_semgrep_findings) AS total_semgrep_findings,
    AVG(total_code) AS avg_code_size,
    AVG(total_commits) AS avg_commits,
    AVG(repo_size_bytes) AS avg_repo_size
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 1. Semgrep Coverage (ACTIVE Only)
SELECT
    COUNT(*) AS total_active_repos,
    COUNT(*) FILTER (WHERE total_semgrep_findings > 0) AS active_repos_with_semgrep,
        (COUNT(*) FILTER (WHERE total_semgrep_findings > 0) * 100.0 / COUNT(*)) AS active_semgrep_coverage_percentage,
    COUNT(*) FILTER (WHERE total_semgrep_findings = 0 AND total_code = 0) AS repos_without_code,
        COUNT(*) FILTER (WHERE total_semgrep_findings = 0 AND total_code > 0) AS repos_with_code_but_no_semgrep
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE';

-- 2. Distribution of Semgrep Findings (ACTIVE Only)
SELECT
    main_language,
    COUNT(*) AS total_repos,
    AVG(total_semgrep_findings) AS avg_findings,
    AVG(repo_size_bytes) AS avg_repo_size,
    AVG(number_of_files) AS avg_file_count
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND total_semgrep_findings > 0
GROUP BY main_language
ORDER BY total_repos DESC;

-- 3. Repositories Without Semgrep Findings (ACTIVE Only)
SELECT
    repo_id,
    main_language,
    repo_size_bytes,
    number_of_files,
    total_code,
    last_commit_date,
    CASE
        WHEN total_code = 0 THEN 'No Code'
        ELSE 'Code Present but No Findings'
        END AS reason_for_no_semgrep
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND total_semgrep_findings = 0
ORDER BY reason_for_no_semgrep, repo_size_bytes DESC;

-- 4. Aggregate Semgrep Findings with Repository Details
SELECT
    main_language,
    COUNT(*) AS total_repos,
    SUM(total_semgrep_findings) AS total_findings,
    AVG(total_semgrep_findings) AS avg_findings,
    AVG(repo_size_bytes) AS avg_repo_size,
    AVG(number_of_files) AS avg_file_count,
    AVG(total_code) AS avg_code_lines
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
GROUP BY main_language
ORDER BY total_findings DESC;

-- 5. High-Risk Repositories Based on Semgrep Findings
SELECT
    repo_id,
    main_language,
    total_semgrep_findings,
    cat_security,
    cat_correctness,
    cat_maintainability,
    repo_size_bytes,
    number_of_files,
    total_code,
    avg_ccn
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND total_semgrep_findings > 50
ORDER BY total_semgrep_findings DESC;

-- 6. Semgrep Findings vs. Repository Characteristics
SELECT
    repo_id,
    main_language,
    total_semgrep_findings,
    repo_size_bytes,
    number_of_files,
    total_code,
    repo_size_bytes / NULLIF(total_semgrep_findings, 1) AS size_per_finding,
    number_of_files / NULLIF(total_semgrep_findings, 1) AS files_per_finding
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND total_semgrep_findings > 0
ORDER BY size_per_finding DESC;

-- 7. Semgrep Findings by Repository Age
SELECT
    repo_id,
    main_language,
    repo_age_days,
    total_semgrep_findings,
    cat_security,
    cat_correctness,
    total_code,
    repo_size_bytes,
    number_of_files
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
ORDER BY repo_age_days DESC, total_semgrep_findings DESC;

-- 8. Repositories Without Code or Semgrep Findings
SELECT
    repo_id,
    main_language,
    repo_size_bytes,
    number_of_files,
    total_code,
    total_semgrep_findings,
    last_commit_date
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND total_code = 0
  AND total_semgrep_findings = 0
ORDER BY repo_size_bytes DESC;

-- 1. Compare Characteristics of Repositories With and Without Main Language Detected
SELECT
    CASE
        WHEN main_language IS NULL THEN 'No Main Language Detected'
        ELSE 'Main Language Detected'
        END AS language_status,
    COUNT(*) AS repo_count,
    AVG(file_count) AS avg_file_count,
    AVG(repo_size_bytes) AS avg_repo_size,
    AVG(number_of_contributors) AS avg_contributors,
    AVG(total_commits) AS avg_commits,
    AVG(total_code) AS avg_code_lines
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
GROUP BY language_status
ORDER BY language_status;

-- 2. Detailed Breakdown of Repositories Without Main Language
SELECT
    repo_id,
    file_count,
    repo_size_bytes,
    number_of_contributors,
    total_commits,
    total_code,
    last_commit_date
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND main_language IS NULL
ORDER BY repo_size_bytes DESC;

-- 3. File Count Distribution for Repositories Without Main Language
SELECT
    file_count,
    COUNT(*) AS repo_count
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND main_language IS NULL
GROUP BY file_count
ORDER BY file_count DESC;

-- 4. Repositories With Main Language Detected
SELECT
    main_language,
    COUNT(*) AS repo_count,
    AVG(file_count) AS avg_file_count,
    AVG(repo_size_bytes) AS avg_repo_size,
    AVG(number_of_contributors) AS avg_contributors,
    AVG(total_commits) AS avg_commits,
    AVG(total_code) AS avg_code_lines
FROM combined_repo_metrics
WHERE ACTIVITY_STATUS = 'ACTIVE'
  AND main_language IS NOT NULL
GROUP BY main_language
ORDER BY repo_count DESC;

WITH metric_bounds AS (
    SELECT
        MIN(executable_lines_of_code)      AS min_loc,
        MAX(executable_lines_of_code)      AS max_loc,
        MIN(avg_cyclomatic_complexity)     AS min_cc,
        MAX(avg_cyclomatic_complexity)     AS max_cc,
        MIN(total_trivy_vulns)             AS min_tv,
        MAX(total_trivy_vulns)             AS max_tv
    FROM combined_repo_metrics
),
     normalized AS (
         SELECT
             crm.repo_id,

             CASE
                 WHEN mb.max_loc = mb.min_loc THEN 0
                 ELSE (crm.executable_lines_of_code - mb.min_loc) / (mb.max_loc - mb.min_loc)
                 END AS loc_norm,

             CASE
                 WHEN mb.max_cc = mb.min_cc THEN 0
                 ELSE (crm.avg_cyclomatic_complexity - mb.min_cc) / (mb.max_cc - mb.min_cc)
                 END AS cc_norm,

             CASE
                 WHEN mb.max_tv = mb.min_tv THEN 0
                 ELSE (crm.total_trivy_vulns - mb.min_tv) / (mb.max_tv - mb.min_tv)
                 END AS tv_norm,

             crm.language_count,
             crm.main_language

         FROM combined_repo_metrics crm
                  CROSS JOIN metric_bounds mb
     )
SELECT
    repo_id,
    loc_norm,
    cc_norm,
    tv_norm,
    language_count,
    main_language,
    (
        0.4 * loc_norm +
        0.4 * cc_norm +
        0.2 * tv_norm
        ) AS technical_debt_score
FROM normalized
ORDER BY technical_debt_score DESC
    LIMIT 10;


