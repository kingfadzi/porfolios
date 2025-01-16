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
