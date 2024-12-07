WITH RankedProjects AS (
    SELECT
        pl.language,
        pm.input_project_id,
        pm.project_id,
        pm.number_of_commits,
        pm.last_commit_date,
        RANK() OVER (PARTITION BY pl.language ORDER BY pm.number_of_commits DESC, pm.last_commit_date DESC) AS rank
    FROM
        project_metrics pm
    INNER JOIN
        programming_languages pl ON pm.project_id = pl.project_id
)
SELECT
    language,
    input_project_id,
    project_id,
    number_of_commits,
    last_commit_date
FROM
    RankedProjects
WHERE
    rank <= 50
ORDER BY
    language,
    rank;
