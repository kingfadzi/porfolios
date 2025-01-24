CREATE MATERIALIZED VIEW java_ecosystem_metrics AS
WITH cloc_aggregated AS (
    SELECT
        repo_id,
        SUM(code) AS total_lines_of_code
    FROM cloc_metrics
    WHERE language != 'SUM'
GROUP BY repo_id
    )
SELECT
    kantra_violations.repo_id AS repository_id,
    kantra_violations.id AS violation_id,
    kantra_violations.ruleset_name AS ruleset_name,
    kantra_violations.rule_name AS rule_name,
    kantra_violations.description AS description,
    kantra_violations.category AS category,
    kantra_violations.effort AS effort,
    kantra_labels.key AS component_type,
    kantra_labels.value AS component_name,
    rbm.component_id AS component_id,
    STRING_AGG(DISTINCT bam.business_app_identifier, ', ' ORDER BY bam.business_app_identifier) AS business_app_identifiers,
    bam.transaction_cycle AS transaction_cycle,
    vcm.web_url AS repository_url,
    cloc.total_lines_of_code,
    br.host_name AS bitbucket_host_name,
    rm.activity_status AS repo_activity_status,
    CASE
        WHEN cloc.total_lines_of_code IS NULL OR cloc.total_lines_of_code < 100
            THEN CASE
                     WHEN rm.repo_size_bytes < 1000000 OR rm.repo_size_bytes IS NULL
                         THEN 'Non-Code -> Empty/Minimal'
                     ELSE 'Non-Code -> Docs/Data'
            END
        ELSE CASE
                 WHEN rm.repo_size_bytes < 1000000 OR rm.repo_size_bytes IS NULL
                     THEN 'Code -> Tiny'
                 WHEN rm.repo_size_bytes < 10000000
                     THEN 'Code -> Small'
                 WHEN rm.repo_size_bytes < 100000000
                     THEN 'Code -> Medium'
                 WHEN rm.repo_size_bytes < 1000000000
                     THEN 'Code -> Large'
                 ELSE 'Code -> Massive'
            END
        END AS classification_label
FROM
    kantra_violations
        LEFT JOIN kantra_violation_labels
                  ON kantra_violations.id = kantra_violation_labels.violation_id
        LEFT JOIN kantra_labels
                  ON kantra_violation_labels.label_id = kantra_labels.id
        LEFT JOIN bitbucket_repositories br
                  ON kantra_violations.repo_id = br.repo_id
        LEFT JOIN repo_business_mapping rbm
                  ON lower(br.project_key) = lower(rbm.project_key)
                      AND lower(br.repo_slug) = lower(rbm.repo_slug)
        LEFT JOIN business_app_mapping bam
                  ON rbm.component_id = bam.component_id
        LEFT JOIN version_control_mapping vcm
                  ON lower(rbm.project_key) = lower(vcm.project_key)
                      AND lower(rbm.repo_slug) = lower(vcm.repo_slug)
        LEFT JOIN cloc_aggregated cloc
                  ON kantra_violations.repo_id = cloc.repo_id
        LEFT JOIN repo_metrics rm
                  ON kantra_violations.repo_id = rm.repo_id
GROUP BY
    kantra_violations.id,
    kantra_violations.ruleset_name,
    kantra_violations.rule_name,
    kantra_violations.description,
    kantra_violations.category,
    kantra_violations.effort,
    kantra_violations.repo_id,
    kantra_labels.key,
    kantra_labels.value,
    rbm.component_id,
    bam.transaction_cycle,
    vcm.web_url,
    br.host_name,
    rm.activity_status,
    cloc.total_lines_of_code,
    rm.repo_size_bytes;
