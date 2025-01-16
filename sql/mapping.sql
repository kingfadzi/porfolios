SELECT
    r.repo_id,
    r.project_key,
    r.repo_slug,
    r.clone_ssh_url,
    cm_v.web_url,
    cm_b.identifier
FROM repo AS r
         JOIN component_mapping AS cm_v
              ON r.project_key = cm_v.project_key
                  AND r.repo_slug  = cm_v.repo_slug
         JOIN component_mapping AS cm_b
              ON cm_v.component_id = cm_b.component_id
WHERE cm_v.mapping_type = 'vs'
  AND cm_b.mapping_type = 'ba';

SELECT
    LOWER(b.project_key) AS pkey,
    LOWER(b.repo_slug)   AS slug,
    cm_v.component_id,
    COUNT(cm_b.identifier) AS identifier_count,
    STRING_AGG(cm_b.identifier, ', ' ORDER BY cm_b.identifier) AS all_identifiers
FROM bitbucket_repositories b
         LEFT JOIN component_mapping cm_v
                   ON  LOWER(cm_v.project_key) = LOWER(b.project_key)
                       AND LOWER(cm_v.repo_slug)   = LOWER(b.repo_slug)
                       AND cm_v.mapping_type       = 'vs'
         LEFT JOIN component_mapping cm_b
                   ON  cm_b.component_id = cm_v.component_id
                       AND cm_b.mapping_type = 'ba'
GROUP BY
    LOWER(b.project_key),
    LOWER(b.repo_slug),
    cm_v.component_id
HAVING
    COUNT(cm_b.identifier) > 1;
