from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DB_URL = "postgresql+psycopg2://postgres:postgres@localhost/gitlab-usage"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Repository(Base):
    __tablename__ = "bitbucket_repositories"
    repo_id = Column(String, primary_key=True)
    repo_name = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    clone_url_ssh = Column(String)
    status = Column(String)
    comment = Column(String)
    updated_on = Column(DateTime)

class LanguageAnalysis(Base):
    __tablename__ = "languages_analysis"
    id = Column(String, primary_key=True)
    repo_id = Column(String, nullable=False)
    language = Column(String, nullable=False)
    percent_usage = Column(Float, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('repo_id', 'language', name='_repo_language_uc'),)

class RepoMetrics(Base):
    __tablename__ = "repo_metrics"
    repo_id = Column(String, primary_key=True)
    repo_size_bytes = Column(Float, nullable=False)
    file_count = Column(Integer, nullable=False)
    total_commits = Column(Integer, nullable=False)
    number_of_contributors = Column(Integer, nullable=False)
    last_commit_date = Column(DateTime)
    repo_age_days = Column(Integer, nullable=False)
    active_branch_count = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
# Lizard Metrics Model
class LizardMetric(Base):
    __tablename__ = "lizard_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    file_name = Column(Text)
    function_name = Column(Text)
    long_name = Column(Text)
    nloc = Column(Integer)
    ccn = Column(Integer)
    token_count = Column(Integer)
    param = Column(Integer)
    function_length = Column(Integer)
    start_line = Column(Integer)
    end_line = Column(Integer)
    __table_args__ = (
        UniqueConstraint("repo_id", "file_name", "function_name", name="lizard_metric_uc"),
    )

# Lizard Summary Model
class LizardSummary(Base):
    __tablename__ = "lizard_summary"
    repo_id = Column(String, primary_key=True)
    total_nloc = Column(Integer)
    avg_ccn = Column(Float)
    total_token_count = Column(Integer)
    function_count = Column(Integer)
    total_ccn = Column(Integer)

# Cloc Metrics Model
class ClocMetric(Base):
    __tablename__ = "cloc_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    language = Column(Text)
    files = Column(Integer)
    blank = Column(Integer)
    comment = Column(Integer)
    code = Column(Integer)
    __table_args__ = (
        UniqueConstraint("repo_id", "language", name="cloc_metric_uc"),
    )

# Checkov Results Model
class CheckovResult(Base):
    __tablename__ = "checkov_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    resource = Column(Text)
    check_name = Column(Text)
    check_result = Column(Text)
    severity = Column(Text)
    __table_args__ = (
        UniqueConstraint("repo_id", "resource", "check_name", name="checkov_result_uc"),
    )

class CheckovSarifResult(Base):
    __tablename__ = "checkov_sarif_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    rule_id = Column(Text)
    rule_name = Column(Text)
    severity = Column(Text)
    file_path = Column(Text)
    start_line = Column(Integer)
    end_line = Column(Integer)
    message = Column(Text)

class DependencyCheckResult(Base):
    __tablename__ = "dependency_check_results"
    id = Column(Integer, primary_key=True, autoincrement=True)  # Auto-incrementing primary key
    repo_id = Column(String, nullable=False)  # Repository ID (foreign key or unique reference)
    cve = Column(String, nullable=False)  # Common Vulnerabilities and Exposures ID
    description = Column(Text, nullable=True)  # Detailed description of the vulnerability
    severity = Column(String, nullable=True)  # Severity level (e.g., High, Medium, Low)
    vulnerable_software = Column(String, nullable=True)  # List of vulnerable software versions
    __table_args__ = (
        UniqueConstraint("repo_id", "cve", name="dependency_check_result_uc"),  # Unique constraint on repo_id and cve
    )

class GrypeResult(Base):
    __tablename__ = "grype_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    cve = Column(String, nullable=False)  # CVE ID or equivalent
    description = Column(Text)
    severity = Column(String, nullable=False)
    package = Column(String, nullable=False)  # Name of the affected package
    version = Column(String, nullable=False)  # Version of the affected package
    file_path = Column(Text)  # File path of the affected artifact
    cvss = Column(Text)  # CVSS scores, serialized as a JSON string
    __table_args__ = (
        UniqueConstraint("repo_id", "cve", "package", "version", name="grype_result_uc"),
    )
