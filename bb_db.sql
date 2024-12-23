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

-- Create lizard_metrics table
DROP TABLE IF EXISTS lizard_metrics;

CREATE TABLE lizard_metrics (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    file_name TEXT,  -- Updated
    function_name TEXT,
    long_name TEXT,
    nloc INTEGER,
    ccn INTEGER,
    token_count INTEGER,
    param INTEGER,
    function_length INTEGER,  -- Updated
    start_line INTEGER,  -- Updated
    end_line INTEGER,  -- Updated
    CONSTRAINT lizard_metrics_unique UNIQUE (repo_id, file_name, function_name)
);

-- Create cloc_metrics table
CREATE TABLE cloc_metrics (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    language TEXT,
    files INTEGER,
    blank INTEGER,
    comment INTEGER,
    code INTEGER,
    CONSTRAINT cloc_metrics_unique UNIQUE (repo_id, language)
);

-- Create checkov_results table
CREATE TABLE checkov_results (
    id SERIAL PRIMARY KEY,                        -- Auto-incrementing primary key
    repo_id INTEGER NOT NULL,                    -- Repository ID (foreign key, not enforced here)
    resource TEXT,                               -- The resource being checked (e.g., S3 bucket, IAM role)
    check_name TEXT,                             -- Name/description of the check
    check_result TEXT,                           -- Result of the check (e.g., PASSED, FAILED)
    severity TEXT,                               -- Severity of the issue (e.g., LOW, MEDIUM, HIGH)
    file_path TEXT,                              -- Path to the file containing the resource
    line_range TEXT,                             -- Range of lines in the file affected by the issue
    CONSTRAINT checkov_results_unique UNIQUE (repo_id, resource, check_name)  -- Ensure no duplicates for the same check
);

CREATE TABLE lizard_summary (
    repo_id INTEGER PRIMARY KEY,  -- repo_id as the primary key
    total_nloc INTEGER,
    avg_ccn FLOAT,
    total_token_count INTEGER,
    function_count INTEGER
);

-- Lizard Metrics: Unique on (repo_id, file, function)
ALTER TABLE lizard_metrics ADD CONSTRAINT lizard_metrics_unique UNIQUE (repo_id, file, function);

-- Cloc Metrics: Unique on (repo_id, language)
ALTER TABLE cloc_metrics ADD CONSTRAINT cloc_metrics_unique UNIQUE (repo_id, language);

-- Checkov Results: Unique on (repo_id, resource, check_name)
ALTER TABLE checkov_results ADD CONSTRAINT checkov_results_unique UNIQUE (repo_id, resource, check_name);

