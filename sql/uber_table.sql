DROP MATERIALIZED VIEW IF EXISTS combined_repo_metrics;

CREATE MATERIALIZED VIEW combined_repo_metrics AS
WITH
all_repos AS (
    SELECT repo_id FROM lizard_summary
    UNION
    SELECT repo_id FROM cloc_metrics
    UNION
    SELECT repo_id FROM checkov_summary
    UNION
    SELECT repo_id FROM trivy_vulnerability
    UNION
    SELECT repo_id FROM semgrep_results
    UNION
    SELECT repo_id FROM repo_metrics
    UNION
    SELECT repo_id FROM go_enry_analysis
    UNION
    SELECT repo_id FROM bitbucket_repositories
),

cloc_agg AS (
    SELECT
        repo_id,
        SUM(files) AS source_code_file_count,
        SUM(blank) AS total_blank,
        SUM(comment) AS total_comment,
        SUM(code) AS total_lines_of_code
    FROM cloc_metrics
    WHERE language != 'SUM'
    GROUP BY repo_id
),

checkov_agg AS (
    SELECT
        repo_id,
        MAX(CASE WHEN check_type = 'ansible' THEN 1 ELSE 0 END)             AS iac_ansible,
        MAX(CASE WHEN check_type = 'azure_pipelines' THEN 1 ELSE 0 END)     AS iac_azure_pipelines,
        MAX(CASE WHEN check_type = 'bitbucket_pipelines' THEN 1 ELSE 0 END) AS iac_bitbucket_pipelines,
        MAX(CASE WHEN check_type = 'circleci_pipelines' THEN 1 ELSE 0 END)  AS iac_circleci_pipelines,
        MAX(CASE WHEN check_type = 'cloudformation' THEN 1 ELSE 0 END)      AS iac_cloudformation,
        MAX(CASE WHEN check_type = 'dockerfile' THEN 1 ELSE 0 END)          AS iac_dockerfile,
        MAX(CASE WHEN check_type = 'github_actions' THEN 1 ELSE 0 END)      AS iac_github_actions,
        MAX(CASE WHEN check_type = 'gitlab_ci' THEN 1 ELSE 0 END)           AS iac_gitlab_ci,
        MAX(CASE WHEN check_type = 'kubernetes' THEN 1 ELSE 0 END)          AS iac_kubernetes,
        MAX(CASE WHEN check_type = 'no-checks' THEN 1 ELSE 0 END)           AS iac_no_checks,
        MAX(CASE WHEN check_type = 'openapi' THEN 1 ELSE 0 END)             AS iac_openapi,
        MAX(CASE WHEN check_type = 'secrets' THEN 1 ELSE 0 END)             AS iac_secrets,
        MAX(CASE WHEN check_type = 'terraform' THEN 1 ELSE 0 END)           AS iac_terraform,
        MAX(CASE WHEN check_type = 'terraform_plan' THEN 1 ELSE 0 END)      AS iac_terraform_plan
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
        COUNT(*) FILTER (WHERE category = 'best-practice')   AS cat_best_practice,
        COUNT(*) FILTER (WHERE category = 'compatibility')   AS cat_compatibility,
        COUNT(*) FILTER (WHERE category = 'correctness')     AS cat_correctness,
        COUNT(*) FILTER (WHERE category = 'maintainability') AS cat_maintainability,
        COUNT(*) FILTER (WHERE category = 'performance')     AS cat_performance,
        COUNT(*) FILTER (WHERE category = 'portability')     AS cat_portability,
        COUNT(*) FILTER (WHERE category = 'security')        AS cat_security
    FROM semgrep_results
    GROUP BY repo_id
),

go_enry_agg AS (
    SELECT
        g.repo_id,
        COUNT(*) AS language_count,
        (
            SELECT x.language
            FROM go_enry_analysis x
            WHERE x.repo_id = g.repo_id
            ORDER BY x.percent_usage DESC, x.language
            LIMIT 1
        ) AS main_language
    FROM go_enry_analysis g
    GROUP BY g.repo_id
),

ba_agg AS (
    SELECT
        cba.component_id,
        cba.project_key,
        cba.repo_slug,
        cba.transaction_cycle,
        STRING_AGG(cba.business_app_identifier, ', ' ORDER BY cba.business_app_identifier)
          AS all_business_apps
    FROM component_business_app cba
    GROUP BY cba.component_id, cba.project_key, cba.repo_slug, cba.transaction_cycle
)

SELECT
    r.repo_id,

    -- Lizard summary columns
    l.total_nloc AS executable_lines_of_code,
    l.avg_ccn    AS avg_cyclomatic_complexity,
    l.total_token_count,
    l.function_count,
    l.total_ccn  AS total_cyclomatic_complexity,

    -- cloc columns
    c.source_code_file_count,
    c.total_blank,
    c.total_comment,
    c.total_lines_of_code,

    -- checkov columns
    ck.iac_ansible,
    ck.iac_azure_pipelines,
    ck.iac_bitbucket_pipelines,
    ck.iac_circleci_pipelines,
    ck.iac_cloudformation,
    ck.iac_dockerfile,
    ck.iac_github_actions,
    ck.iac_gitlab_ci,
    ck.iac_kubernetes,
    ck.iac_no_checks,
    ck.iac_openapi,
    ck.iac_secrets,
    ck.iac_terraform,
    ck.iac_terraform_plan,

    -- trivy columns
    t.total_trivy_vulns,
    t.trivy_critical,
    t.trivy_high,
    t.trivy_medium,
    t.trivy_low,

    -- semgrep columns
    s.total_semgrep_findings,
    s.cat_best_practice,
    s.cat_compatibility,
    s.cat_correctness,
    s.cat_maintainability,
    s.cat_performance,
    s.cat_portability,
    s.cat_security,

    -- go_enry columns
    e.language_count,
    e.main_language,

    -- repo_metrics columns
    rm.repo_size_bytes,
    rm.file_count,
    rm.total_commits,
    rm.number_of_contributors,
    rm.activity_status,
    rm.last_commit_date,
    rm.repo_age_days,
    rm.active_branch_count,
    rm.updated_at,

    -- bitbucket columns
    b.host_name,
    b.app_id,
    b.project_key,
    b.repo_slug,
    b.tc_cluster,
    b.tc,
    b.clone_url_ssh,
    b.status,
    b.comment,

    -- classification_label logic (truncated for brevity, same as your example)
    CASE
        WHEN e.main_language IS NULL THEN
            CASE
                WHEN (c.total_lines_of_code < 100)
                    AND (rm.file_count < 10 OR rm.file_count IS NULL)
                    AND (rm.repo_size_bytes < 1000000 OR rm.repo_size_bytes IS NULL)
                    THEN 'Non-Code -> Empty/Minimal'
                ELSE 'Non-Code -> Docs/Data'
                END
        ELSE
            CASE
                WHEN (c.total_lines_of_code < 500)
                    AND (rm.file_count < 20 OR rm.file_count IS NULL)
                    AND (rm.repo_size_bytes < 1000000 OR rm.repo_size_bytes IS NULL)
                    THEN 'Code -> Tiny'
                WHEN (c.total_lines_of_code < 5000)
                    AND (rm.file_count < 200 OR rm.file_count IS NULL)
                    AND (rm.repo_size_bytes < 10000000 OR rm.repo_size_bytes IS NULL)
                    THEN 'Code -> Small'
                WHEN (c.total_lines_of_code < 50000)
                    AND (rm.file_count < 1000 OR rm.file_count IS NULL)
                    AND (rm.repo_size_bytes < 100000000 OR rm.repo_size_bytes IS NULL)
                    THEN 'Code -> Medium'
                WHEN (c.total_lines_of_code < 100000)
                    AND (rm.file_count < 5000 OR rm.file_count IS NULL)
                    AND (rm.repo_size_bytes < 1000000000 OR rm.repo_size_bytes IS NULL)
                    THEN 'Code -> Large'
                WHEN c.total_lines_of_code >= 100000
                    OR rm.file_count >= 5000
                    OR rm.repo_size_bytes >= 1000000000
                    THEN 'Code -> Massive'
                ELSE 'Unclassified'
                END
        END AS classification_label,

    ba.all_business_apps AS business_app_identifiers,
    ba.transaction_cycle AS transaction_cycle

FROM all_repos r
         LEFT JOIN lizard_summary         l  ON r.repo_id = l.repo_id
         LEFT JOIN cloc_agg               c  ON r.repo_id = c.repo_id
         LEFT JOIN checkov_agg            ck ON r.repo_id = ck.repo_id
         LEFT JOIN trivy_agg              t  ON r.repo_id = t.repo_id
         LEFT JOIN semgrep_agg            s  ON r.repo_id = s.repo_id
         LEFT JOIN go_enry_agg            e  ON r.repo_id = e.repo_id
         LEFT JOIN repo_metrics           rm ON r.repo_id = rm.repo_id
         LEFT JOIN bitbucket_repositories b  ON r.repo_id = b.repo_id

         LEFT JOIN ba_agg ba
                   ON ba.project_key   = b.project_key
                       AND ba.repo_slug     = b.repo_slug

ORDER BY r.repo_id;
