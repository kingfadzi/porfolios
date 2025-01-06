CREATE MATERIALIZED VIEW uber_dataset_mv AS
SELECT
    r.repo_id,
    r.repo_name,
    r.repo_slug,
    r.status AS repo_status,
    rm.activity_status,
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
    cs.check_type AS check_type,
    cs.passed AS passed,
    cs.failed AS failed,
    cs.skipped AS skipped,
    cs.resource_count AS resource_count,
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


CREATE INDEX idx_repository_repo_id ON repository(repo_id);
CREATE INDEX idx_go_enry_analysis_repo_id ON go_enry_analysis(repo_id);
CREATE INDEX idx_repo_metrics_repo_id ON repo_metrics(repo_id);
CREATE INDEX idx_lizard_summary_repo_id ON lizard_summary(repo_id);
CREATE INDEX idx_cloc_metrics_repo_id ON cloc_metrics(repo_id);
CREATE INDEX idx_grype_results_repo_id ON grype_results(repo_id);
CREATE INDEX idx_checkov_summary_repo_id ON checkov_summary(repo_id);
CREATE INDEX idx_trivy_vulnerability_repo_id ON trivy_vulnerability(repo_id);
CREATE INDEX idx_semgrep_results_repo_id ON semgrep_results(repo_id);
