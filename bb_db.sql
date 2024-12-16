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
