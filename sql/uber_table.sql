CREATE OR REPLACE VIEW combined_repo_metrics AS
WITH

-- 1) Enumerate all repos from across the various tables.
all_repos AS (
    SELECT repo_id FROM lizard_summary
    UNION
    SELECT repo_id FROM cloc_metrics
    UNION
    SELECT repo_id FROM grype_results
    UNION
    SELECT repo_id FROM checkov_summary
    UNION
    SELECT repo_id FROM trivy_vulnerability
    UNION
    SELECT repo_id FROM semgrep_results
    UNION
    SELECT repo_id FROM repo_metrics    -- Include repos found in repo_metrics
),

-- 2) Example aggregations for cloc_metrics, grype, etc.
cloc_agg AS (
    SELECT
        repo_id,
        SUM(files)   AS total_files,
        SUM(blank)   AS total_blank,
        SUM(comment) AS total_comment,
        SUM(code)    AS total_code
    FROM cloc_metrics
    GROUP BY repo_id
),
grype_agg AS (
    SELECT
        repo_id,
        COUNT(*) AS total_grype_vulns,
        COUNT(*) FILTER (WHERE severity = 'Critical') AS critical_vulns,
        COUNT(*) FILTER (WHERE severity = 'High')     AS high_vulns,
        COUNT(*) FILTER (WHERE severity = 'Medium')   AS medium_vulns,
        COUNT(*) FILTER (WHERE severity = 'Low')      AS low_vulns
    FROM grype_results
    GROUP BY repo_id
),
checkov_agg AS (
    SELECT
        repo_id,
        SUM(passed)  AS total_passed,
        SUM(failed)  AS total_failed,
        SUM(skipped) AS total_skipped,
        SUM(resource_count) AS total_resources,
        SUM(parsing_errors) AS total_parsing_errors
    FROM checkov_summary
    GROUP BY repo_id
),
trivy_agg AS (
    SELECT
        repo_id,
        COUNT(*) AS total_trivy_vulns,
        COUNT(*) FILTER (WHERE severity = 'CRITICAL') AS trivy_critical,
        COUNT(*) FILTER (WHERE severity = 'HIGH')     AS trivy_high,
        COUNT(*) FILTER (WHERE severity = 'MEDIUM')   AS trivy_medium,
        COUNT(*) FILTER (WHERE severity = 'LOW')      AS trivy_low
    FROM trivy_vulnerability
    GROUP BY repo_id
),
semgrep_agg AS (
    SELECT
        repo_id,
        COUNT(*) AS total_semgrep_findings,
        COUNT(*) FILTER (WHERE severity = 'ERROR')   AS semgrep_error,
        COUNT(*) FILTER (WHERE severity = 'WARNING') AS semgrep_warning,
        COUNT(*) FILTER (WHERE severity = 'INFO')    AS semgrep_info
    FROM semgrep_results
    GROUP BY repo_id
)

-- 3) Final SELECT: 
--    Join all aggregated sub-results + the lizard_summary + repo_metrics
SELECT
    r.repo_id,

    -- lizard_summary is already 1:1 with repo_id
    l.total_nloc,
    l.avg_ccn,
    l.total_token_count,
    l.function_count,
    l.total_ccn     AS total_ccn_lizard,

    -- From cloc_agg
    c.total_files,
    c.total_blank,
    c.total_comment,
    c.total_code,

    -- From grype_agg
    g.total_grype_vulns,
    g.critical_vulns,
    g.high_vulns,
    g.medium_vulns,
    g.low_vulns,

    -- From checkov_agg
    ck.total_passed,
    ck.total_failed,
    ck.total_skipped,
    ck.total_resources,
    ck.total_parsing_errors,

    -- From trivy_agg
    t.total_trivy_vulns,
    t.trivy_critical,
    t.trivy_high,
    t.trivy_medium,
    t.trivy_low,

    -- From semgrep_agg
    s.total_semgrep_findings,
    s.semgrep_error,
    s.semgrep_warning,
    s.semgrep_info,

    -- Directly from repo_metrics table (no aggregation needed)
    rm.repo_size_bytes,
    rm.file_count,
    rm.total_commits,
    rm.number_of_contributors,
    rm.activity_status,
    rm.last_commit_date,
    rm.repo_age_days,
    rm.active_branch_count,
    rm.updated_at

FROM all_repos r
-- Join lizard_summary
LEFT JOIN lizard_summary       l  ON r.repo_id = l.repo_id
-- Join cloc_agg
LEFT JOIN cloc_agg            c  ON r.repo_id = c.repo_id
-- Join grype_agg
LEFT JOIN grype_agg           g  ON r.repo_id = g.repo_id
-- Join checkov_agg
LEFT JOIN checkov_agg         ck ON r.repo_id = ck.repo_id
-- Join trivy_agg
LEFT JOIN trivy_agg           t  ON r.repo_id = t.repo_id
-- Join semgrep_agg
LEFT JOIN semgrep_agg         s  ON r.repo_id = s.repo_id
-- Finally, join repo_metrics (1 row per repo)
LEFT JOIN repo_metrics        rm ON r.repo_id = rm.repo_id

ORDER BY r.repo_id;