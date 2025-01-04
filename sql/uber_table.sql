-- Step 1: Create the Partitioned Table
CREATE TABLE uber_dataset_partitioned (
    repo_id TEXT NOT NULL,
    repo_name TEXT,
    repo_slug TEXT,
    repo_status TEXT, -- For ingestion status
    activity_status TEXT NOT NULL, -- Partition key (active/inactive)
    last_updated TIMESTAMP,
    primary_language TEXT,
    language_usage_percent FLOAT,
    repo_size_bytes NUMERIC,
    file_count INT,
    total_commits INT,
    number_of_contributors INT,
    last_commit_date TIMESTAMP,
    repo_age_days INT,
    active_branch_count INT,
    total_lines_of_code INT,
    avg_complexity_score FLOAT,
    total_complexity_score INT,
    total_functions INT,
    cloc_language TEXT,
    cloc_code_lines INT,
    cloc_comment_lines INT,
    cloc_blank_lines INT,
    grype_id INT,
    grype_cve TEXT,
    grype_severity TEXT,
    grype_package TEXT,
    grype_version TEXT,
    grype_language TEXT,
    checkov_id INT,
    check_type TEXT,
    checkov_language TEXT,
    passed INT,
    failed INT,
    skipped INT,
    resource_count INT,
    trivy_id INT,
    trivy_target TEXT,
    trivy_resource_class TEXT,
    trivy_resource_type TEXT,
    trivy_vulnerability_id TEXT,
    trivy_pkg_name TEXT,
    trivy_installed_version TEXT,
    trivy_fixed_version TEXT,
    trivy_severity TEXT,
    semgrep_id INT,
    semgrep_path TEXT,
    semgrep_start_line INT,
    semgrep_end_line INT,
    semgrep_rule_id TEXT,
    semgrep_severity TEXT,
    semgrep_message TEXT,
    semgrep_category TEXT
) PARTITION BY LIST (activity_status);

-- Step 2: Create Partitions
CREATE TABLE uber_dataset_active PARTITION OF uber_dataset_partitioned
FOR VALUES IN ('active');

CREATE TABLE uber_dataset_inactive PARTITION OF uber_dataset_partitioned
FOR VALUES IN ('inactive');

-- Step 3: Populate the Partitioned Table
INSERT INTO uber_dataset_partitioned (
    repo_id,
    repo_name,
    repo_slug,
    repo_status,
    activity_status,
    last_updated,
    primary_language,
    language_usage_percent,
    repo_size_bytes,
    file_count,
    total_commits,
    number_of_contributors,
    last_commit_date,
    repo_age_days,
    active_branch_count,
    total_lines_of_code,
    avg_complexity_score,
    total_complexity_score,
    total_functions,
    cloc_language,
    cloc_code_lines,
    cloc_comment_lines,
    cloc_blank_lines,
    grype_id,
    grype_cve,
    grype_severity,
    grype_package,
    grype_version,
    grype_language,
    checkov_id,
    check_type,
    checkov_language,
    passed,
    failed,
    skipped,
    resource_count,
    trivy_id,
    trivy_target,
    trivy_resource_class,
    trivy_resource_type,
    trivy_vulnerability_id,
    trivy_pkg_name,
    trivy_installed_version,
    trivy_fixed_version,
    trivy_severity,
    semgrep_id,
    semgrep_path,
    semgrep_start_line,
    semgrep_end_line,
    semgrep_rule_id,
    semgrep_severity,
    semgrep_message,
    semgrep_category
)
SELECT 
    r.repo_id,
    r.repo_name,
    r.repo_slug,
    r.status AS repo_status,
    CASE 
        WHEN rm.last_commit_date >= CURRENT_DATE - INTERVAL '12 months' THEN 'active'
        ELSE 'inactive'
    END AS activity_status,
    r.updated_on AS last_updated,
    gm.language AS primary_language,
    gm.percent_usage AS language_usage_percent,
    rm.repo_size_bytes,
    rm.file_count,
    rm.total_commits,
    rm.number_of_contributors,
    rm.last_commit_date,
    rm.repo_age_days,
    rm.active_branch_count,
    ls.total_nloc AS total_lines_of_code,
    ls.avg_ccn AS avg_complexity_score,
    ls.total_ccn AS total_complexity_score,
    ls.function_count AS total_functions,
    cm.language AS cloc_language,
    cm.code AS cloc_code_lines,
    cm.comment AS cloc_comment_lines,
    cm.blank AS cloc_blank_lines,
    gr.id AS grype_id,
    gr.cve AS grype_cve,
    gr.severity AS grype_severity,
    gr.package AS grype_package,
    gr.version AS grype_version,
    gr.language AS grype_language,
    cs.id AS checkov_id,
    cs.check_type AS checkov_check_type,
    cs.language AS checkov_language,
    cs.passed AS checkov_passed,
    cs.failed AS checkov_failed,
    cs.skipped AS checkov_skipped,
    cs.resource_count AS checkov_resource_count,
    tv.id AS trivy_id,
    tv.target AS trivy_target,
    tv.resource_class AS trivy_resource_class,
    tv.resource_type AS trivy_resource_type,
    tv.vulnerability_id AS trivy_vulnerability_id,
    tv.pkg_name AS trivy_pkg_name,
    tv.installed_version AS trivy_installed_version,
    tv.fixed_version AS trivy_fixed_version,
    tv.severity AS trivy_severity,
    sr.id AS semgrep_id,
    sr.path AS semgrep_path,
    sr.start_line AS semgrep_start_line,
    sr.end_line AS semgrep_end_line,
    sr.rule_id AS semgrep_rule_id,
    sr.severity AS semgrep_severity,
    sr.message AS semgrep_message,
    sr.category AS semgrep_category
FROM 
    repository r
LEFT JOIN 
    go_enry_analysis gm ON r.repo_id = gm.repo_id
LEFT JOIN 
    repo_metrics rm ON r.repo_id = rm.repo_id
LEFT JOIN 
    lizard_summary ls ON r.repo_id = ls.repo_id
LEFT JOIN 
    cloc_metrics cm ON r.repo_id = cm.repo_id
LEFT JOIN 
    grype_results gr ON r.repo_id = gr.repo_id
LEFT JOIN 
    checkov_summary cs ON r.repo_id = cs.repo_id
LEFT JOIN 
    trivy_vulnerability tv ON r.repo_id = tv.repo_id
LEFT JOIN 
    semgrep_results sr ON r.repo_id = sr.repo_id;

-- Step 4: Add Indexes
CREATE INDEX idx_active_repo_id ON uber_dataset_active(repo_id);
CREATE INDEX idx_inactive_repo_id ON uber_dataset_inactive(repo_id);

CREATE INDEX idx_last_commit_active ON uber_dataset_active(last_commit_date);
