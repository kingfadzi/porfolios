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
    repo_id VARCHAR PRIMARY KEY,
    repo_name VARCHAR NOT NULL,
    repo_slug VARCHAR NOT NULL,
    project_key VARCHAR NOT NULL,
    clone_url_ssh VARCHAR,
    host_name VARCHAR,
    app_id VARCHAR,
    tc_cluster VARCHAR,
    tc VARCHAR,
    status VARCHAR,
    comment VARCHAR,
    updated_on TIMESTAMP
);

CREATE TABLE go_enry_analysis (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    language VARCHAR NOT NULL,
    percent_usage FLOAT NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (repo_id, language)
);

CREATE TABLE repo_metrics (
    repo_id VARCHAR PRIMARY KEY,
    repo_size_bytes FLOAT NOT NULL,
    activity_status VARCHAR,
    file_count INTEGER NOT NULL,
    total_commits INTEGER NOT NULL,
    number_of_contributors INTEGER NOT NULL,
    last_commit_date TIMESTAMP,
    repo_age_days INTEGER NOT NULL,
    active_branch_count INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lizard_metrics (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
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
    repo_id VARCHAR NOT NULL,
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
    repo_id VARCHAR NOT NULL,                    -- Repository ID (foreign key, not enforced here)
    resource TEXT,                               -- The resource being checked (e.g., S3 bucket, IAM role)
    check_name TEXT,                             -- Name/description of the check
    check_result TEXT,                           -- Result of the check (e.g., PASSED, FAILED)
    severity TEXT,                               -- Severity of the issue (e.g., LOW, MEDIUM, HIGH)
    file_path TEXT,                              -- Path to the file containing the resource
    line_range TEXT,                             -- Range of lines in the file affected by the issue
    CONSTRAINT checkov_results_unique UNIQUE (repo_id, resource, check_name)  -- Ensure no duplicates for the same check
);

CREATE TABLE lizard_summary (
    repo_id VARCHAR PRIMARY KEY,  -- repo_id as the primary key
    total_nloc INTEGER,
    avg_ccn FLOAT,
    total_token_count INTEGER,
    function_count INTEGER,
    total_ccn INTEGER
);

CREATE TABLE checkov_sarif_results (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    rule_id TEXT NOT NULL,
    rule_name TEXT,
    severity TEXT,
    file_path TEXT,
    start_line INTEGER,
    end_line INTEGER,
    message TEXT,
    CONSTRAINT checkov_sarif_results_unique UNIQUE (repo_id, rule_id, file_path, start_line, end_line)
);

CREATE TABLE dependency_check_results (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR(255) NOT NULL,
    cve VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(50),
    vulnerable_software JSONB,
    CONSTRAINT dependency_check_results_uc UNIQUE (repo_id, cve)
);

CREATE TABLE grype_results (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    cve VARCHAR NOT NULL,
    description TEXT,
    severity VARCHAR NOT NULL,
    language VARCHAR NOT NULL,
    package VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    fix_versions TEXT,
    fix_state TEXT,
    file_path TEXT,
    cvss TEXT,
    CONSTRAINT grype_result_uc UNIQUE (repo_id, cve, package, version)
);

CREATE TABLE checkov_summary (
    id SERIAL PRIMARY KEY,
    repo_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    passed INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    resource_count INTEGER DEFAULT 0,
    parsing_errors INTEGER DEFAULT 0,
    CONSTRAINT uq_repo_check UNIQUE (repo_id, check_type)
);

CREATE TABLE checkov_files (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    check_type VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_abs_path VARCHAR,
    resource_count INTEGER DEFAULT 0 NOT NULL,
    UNIQUE (repo_id, check_type, file_path)
);

CREATE TABLE checkov_checks (
    id SERIAL PRIMARY KEY,
    repo_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    check_type TEXT NOT NULL,
    check_id TEXT NOT NULL,
    check_name TEXT,
    result TEXT,
    severity TEXT,
    resource TEXT,
    guideline TEXT,
    start_line INTEGER,
    end_line INTEGER,
    CONSTRAINT uq_repo_check_id UNIQUE (repo_id, file_path, check_type, check_id)
);

CREATE TABLE trivy_vulnerability (
    id SERIAL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    target VARCHAR NOT NULL,
    resource_class VARCHAR,  -- e.g., config, lang-pkgs
    resource_type VARCHAR,   -- e.g., dockerfile, terraform
    vulnerability_id VARCHAR NOT NULL,
    pkg_name VARCHAR,
    installed_version VARCHAR,
    fixed_version VARCHAR,
    severity VARCHAR NOT NULL,
    primary_url VARCHAR,
    description TEXT,
    CONSTRAINT uq_repo_vuln_pkg UNIQUE (repo_id, vulnerability_id, pkg_name)
);

CREATE TABLE analysis_execution_log (
    id SERIAL PRIMARY KEY,
    method_name VARCHAR NOT NULL,
    stage VARCHAR,
    run_id VARCHAR,
    repo_id VARCHAR,
    status VARCHAR NOT NULL,
    message TEXT,
    execution_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration FLOAT NOT NULL
);

CREATE TABLE semgrep_results (
     id SERIAL PRIMARY KEY,
     repo_id VARCHAR NOT NULL,
     path VARCHAR NOT NULL,
     start_line INT NOT NULL,
     end_line INT NOT NULL,
     rule_id VARCHAR NOT NULL,
     severity VARCHAR NOT NULL,
     message TEXT,
     category VARCHAR,
     subcategory TEXT,
     technology VARCHAR,
     cwe TEXT,
     likelihood VARCHAR,
     impact VARCHAR,
     confidence VARCHAR,
     UNIQUE (repo_id, path, start_line, rule_id)
);
CREATE TABLE component_mapping (
   id SERIAL PRIMARY KEY,
   component_id   INTEGER,
   component_name VARCHAR,
   tc            VARCHAR,
   mapping_type   VARCHAR,
   instance_url   VARCHAR,
   tool_type      VARCHAR,
   name           VARCHAR,
   identifier     VARCHAR,
   web_url        VARCHAR,
   project_key    VARCHAR,
   repo_slug      VARCHAR
);

DROP TABLE IF EXISTS business_app_mapping;

CREATE TABLE business_app_mapping (
  id SERIAL PRIMARY KEY,
  component_id INTEGER NOT NULL,
  transaction_cycle VARCHAR NOT NULL,
  component_name VARCHAR NOT NULL,
  business_app_identifier VARCHAR NOT NULL
);

DROP TABLE IF EXISTS version_control_mapping;

CREATE TABLE version_control_mapping (
 id SERIAL PRIMARY KEY,
 component_id INTEGER NOT NULL,
 project_key VARCHAR NOT NULL,
 repo_slug VARCHAR NOT NULL,
 web_url VARCHAR
);

DROP TABLE IF EXISTS repo_business_mapping;

CREATE TABLE repo_business_mapping (
   id SERIAL PRIMARY KEY,
   component_id INTEGER NOT NULL,
   project_key VARCHAR NOT NULL,
   repo_slug VARCHAR NOT NULL,
   business_app_identifier VARCHAR NOT NULL
);

CREATE TABLE kantra_rulesets (
    name TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE kantra_violations (
    id SERIAL PRIMARY KEY,
    ruleset_name TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    effort INTEGER,
    repo_id TEXT NOT NULL,
    UNIQUE (repo_id, ruleset_name, rule_name, description)
);

CREATE TABLE kantra_labels (
    id SERIAL PRIMARY KEY,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    UNIQUE (key, value)
);

CREATE TABLE kantra_violation_labels (
     violation_id INT NOT NULL,
     label_id INT NOT NULL,
     PRIMARY KEY (violation_id, label_id)
);
