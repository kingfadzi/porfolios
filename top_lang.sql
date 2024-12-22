WITH size_threshold AS (
    SELECT
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY repo_size_bytes) AS top_10_percent_size
FROM repo_metrics
    ),
    ranked_java_apps AS (
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
    r.total_commits DESC,        -- Most commits
    r.number_of_contributors DESC, -- Most contributors
    r.last_commit_date DESC,     -- Latest commit date
    r.repo_size_bytes DESC       -- Larger size
    ) AS rank
FROM repo_metrics r
    JOIN language_analysis l
ON r.repo_id = l.repo_id
    CROSS JOIN size_threshold t
WHERE l.language_name = 'Java'           -- Focus on Java repositories
  AND l.percent_usage >= 50              -- Java must be dominant
  AND r.repo_size_bytes >= t.top_10_percent_size -- Repository must be large
    )

SELECT
    repo_id,
    repo_size_bytes,
    number_of_contributors,
    total_commits,
    last_commit_date,
    language_name,
    percent_usage
FROM ranked_java_apps
WHERE rank <= 5  -- Return the top N repositories
ORDER BY rank;
