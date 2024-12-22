WITH ranked_repos AS (
    SELECT
        r.repo_id,
        r.repo_size_bytes,
        r.number_of_contributors,
        r.total_commits,
        r.last_commit_date,
        l.language_name,
        l.percent_usage,
        RANK() OVER (
            ORDER BY
                l.percent_usage DESC,
                r.repo_size_bytes DESC,
                r.number_of_contributors DESC,
                r.total_commits DESC,
                r.last_commit_date DESC
        ) AS rank
    FROM repo_metrics r
             JOIN project_languages l
                  ON r.repo_id = l.project_id  -- Adjust this join condition if necessary
    WHERE l.language_name = 'Java'  -- Replace 'Java' with the desired language
)

SELECT
    repo_id,
    repo_size_bytes,
    number_of_contributors,
    total_commits,
    last_commit_date,
    language_name,
    percent_usage
FROM ranked_repos
WHERE rank <= 5  -- Adjust this to return the top N repositories
ORDER BY rank;
