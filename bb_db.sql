-- Table for projects
CREATE TABLE bitbucket_projects (
    project_key TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    description TEXT,
    is_private BOOLEAN,
    created_on TIMESTAMP,
    updated_on TIMESTAMP
);

-- Table for repositories
CREATE TABLE bitbucket_repositories (
    repo_id TEXT PRIMARY KEY,
    project_key TEXT REFERENCES bitbucket_projects(project_key),
    repo_name TEXT NOT NULL,
    repo_slug TEXT NOT NULL,
    clone_url_https TEXT,
    clone_url_ssh TEXT,
    language TEXT,
    size BIGINT,
    forks INT,
    created_on TIMESTAMP,
    updated_on TIMESTAMP
);
CREATE TABLE languages_analysis (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    language VARCHAR NOT NULL,
    percent_usage FLOAT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repo_id, language)
);
CREATE TABLE repo_metrics (
    repo_id VARCHAR PRIMARY KEY,
    repo_size_bytes FLOAT NOT NULL,
    file_count INTEGER NOT NULL,
    total_commits INTEGER NOT NULL,
    number_of_contributors INTEGER NOT NULL,
    last_commit_date TIMESTAMP NULL,
    repo_age_days INTEGER NOT NULL,
    active_branch_count INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CASE
WHEN size BETWEEN 0 AND 999 THEN '<1k'
WHEN size BETWEEN 1000 AND 50000 THEN '1k-50k'
WHEN size BETWEEN 50001 AND 100000 THEN '50k-100k'
WHEN size BETWEEN 100001 AND 200000 THEN '100k-200k'
WHEN size BETWEEN 200001 AND 300000 THEN '200k-300k'
WHEN size BETWEEN 300001 AND 400000 THEN '300k-400k'
WHEN size BETWEEN 400001 AND 500000 THEN '400k-500k'
WHEN size BETWEEN 500001 AND 600000 THEN '500k-600k'
WHEN size BETWEEN 600001 AND 700000 THEN '600k-700k'
WHEN size BETWEEN 700001 AND 800000 THEN '700k-800k'
WHEN size BETWEEN 800001 AND 900000 THEN '800k-900k'
WHEN size BETWEEN 900001 AND 1000000000 THEN '900k-1g'
WHEN size BETWEEN 1000000001 AND 2000000000 THEN '1g-2g'
WHEN size > 2000000001 THEN '2g+'
END

CASE
WHEN size BETWEEN 0 AND 50000 THEN '0-50k'
WHEN size BETWEEN 50001 AND 200000 THEN '50k-200k'
WHEN size BETWEEN 200001 AND 600000 THEN '200k-600k'
WHEN size BETWEEN 600001 AND 1000000 THEN '600k-1000k'
WHEN size BETWEEN 1000001 AND 2000000000 THEN '1000k-2g'
WHEN size > 2000000001 THEN '>2g'
END

CASE
    WHEN last_commit_date >= NOW() - INTERVAL '1 month' THEN 'Active (<1 month)'
    WHEN last_commit_date >= NOW() - INTERVAL '3 months' THEN '1-3 months'
    WHEN last_commit_date >= NOW() - INTERVAL '6 months' THEN '3-6 months'
    WHEN last_commit_date >= NOW() - INTERVAL '1 year' THEN '6-12 months'
    WHEN last_commit_date >= NOW() - INTERVAL '2 years' THEN '1-2 years'
    ELSE 'Over 2 years'
END

CASE
WHEN contributors BETWEEN 0 AND 0 THEN '0 contributors'
WHEN contributors BETWEEN 1 AND 1 THEN '1 contributor'
WHEN contributors BETWEEN 2 AND 5 THEN '2-5 contributors'
WHEN contributors BETWEEN 6 AND 10 THEN '6-10 contributors'
WHEN contributors BETWEEN 11 AND 20 THEN '11-20 contributors'
WHEN contributors BETWEEN 21 AND 50 THEN '21-50 contributors'
WHEN contributors BETWEEN 51 AND 100 THEN '51-100 contributors'
WHEN contributors BETWEEN 101 AND 500 THEN '101-500 contributors'
WHEN contributors > 501 THEN '501+ contributors'
END

CASE
WHEN total_commits BETWEEN 0 AND 0 THEN '0 commits'
WHEN total_commits BETWEEN 1 AND 10 THEN '1-10 commits'
WHEN total_commits BETWEEN 11 AND 50 THEN '11-50 commits'
WHEN total_commits BETWEEN 51 AND 100 THEN '51-100 commits'
WHEN total_commits BETWEEN 101 AND 500 THEN '101-500 commits'
WHEN total_commits BETWEEN 501 AND 1000 THEN '501-1000 commits'
WHEN total_commits BETWEEN 1001 AND 5000 THEN '1001-5000 commits'
WHEN total_commits BETWEEN 5001 AND 10000 THEN '5001-10000 commits'
WHEN total_commits > 10001 THEN '10001+ commits'
END

CASE
WHEN file_count BETWEEN 0 AND 0 THEN '0 files'
WHEN file_count BETWEEN 1 AND 10 THEN '1-10 files'
WHEN file_count BETWEEN 11 AND 50 THEN '11-50 files'
WHEN file_count BETWEEN 51 AND 100 THEN '51-100 files'
WHEN file_count BETWEEN 101 AND 500 THEN '101-500 files'
WHEN file_count BETWEEN 501 AND 1000 THEN '501-1000 files'
WHEN file_count BETWEEN 1001 AND 5000 THEN '1001-5000 files'
WHEN file_count BETWEEN 5001 AND 10000 THEN '5001-10000 files'
WHEN file_count > 10001 THEN '10001+ files'
END
