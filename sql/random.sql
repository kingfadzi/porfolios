UPDATE projects
SET repo_id = REGEXP_REPLACE(
        gitlab_project_url,
        '^https?://[^/]+/org/(.*?)/?$',
        '\1'
              );

UPDATE repositories r
SET
    tc_cluster = p.tc_cluster,
    tc         = p.tc,
    app_id     = p.app_id
    FROM projects p
WHERE r.repo_id = p.repo_id;
