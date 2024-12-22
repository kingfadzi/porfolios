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
    l.language,
    l.percent_usage,
    RANK() OVER (
    ORDER BY
    r.last_commit_date DESC,     -- Most recent activity first
    r.total_commits DESC,        -- Most commits next
    r.number_of_contributors DESC, -- More contributors after that
    r.repo_size_bytes DESC       -- Larger repositories last
    ) AS rank
FROM repo_metrics r
    JOIN languages_analysis l
ON r.repo_id = l.repo_id
    CROSS JOIN size_threshold t
WHERE l.language = 'Java'              -- Focus on Java repositories
  AND l.percent_usage >= 50            -- Java must be dominant
  AND r.repo_size_bytes >= t.top_10_percent_size -- Repository must be large
    )

SELECT
    repo_id,
    repo_size_bytes,
    number_of_contributors,
    total_commits,
    last_commit_date,
    language,
    percent_usage
FROM ranked_java_apps
WHERE rank <= 5  -- Return the top N repositories
ORDER BY rank;
