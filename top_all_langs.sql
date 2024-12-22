WITH size_threshold AS (
    SELECT
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY repo_size_bytes) AS top_10_percent_size
FROM repo_metrics
    ),
    ranked_repos AS (
SELECT
    r.repo_id,
    r.repo_size_bytes,
    r.number_of_contributors,
    r.total_commits,
    r.last_commit_date,
    l.language,
    l.percent_usage,
    p.repo_url,
    RANK() OVER (
    PARTITION BY l.language               -- Rank repositories within each language
    ORDER BY
    r.last_commit_date DESC,          -- Most recent activity first
    r.total_commits DESC,             -- Most commits next
    r.number_of_contributors DESC,    -- More contributors after that
    r.repo_size_bytes DESC            -- Larger repositories last
    ) AS rank
FROM repo_metrics r
    JOIN languages_analysis l
ON r.repo_id = l.repo_id
    JOIN repos p
    ON r.repo_id = p.repo_id                -- Join with the repos table to get the URL
    CROSS JOIN size_threshold t
WHERE l.percent_usage >= 50                  -- Language must be dominant
  AND r.repo_size_bytes >= t.top_10_percent_size -- Repository must be large
    )

SELECT
    repo_id,
    repo_url,
    repo_size_bytes,
    number_of_contributors,
    total_commits,
    last_commit_date,
    language,
    percent_usage
FROM ranked_repos
WHERE rank <= 100  -- Return the top 100 repositories for each language
ORDER BY language, rank;
