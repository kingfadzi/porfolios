import logging
import os
import re
import subprocess
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, UniqueConstraint, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from git import Repo
import pytz

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database setup
DB_URL = "postgresql+psycopg2://postgres:postgres@localhost/gitlab-usage"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ORM Models
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

# Utility Functions
def set_repo_status(session, repo, status, comment):
    """Update repository status and comment."""
    repo.status = status
    repo.comment = comment
    repo.updated_on = datetime.utcnow()
    session.commit()
    logger.info(f"Repo {repo.repo_name}: status updated to {status}")

def clone_repository(repo):
    """Clone repository into a temporary directory."""
    logger.info(f"Cloning repository {repo.repo_name}...")
    base_dir = "/mnt/tmpfs/cloned_repositories"
    repo_dir = f"{base_dir}/{repo.repo_slug}"
    os.makedirs(base_dir, exist_ok=True)
    subprocess.run(f"rm -rf {repo_dir} && git clone {repo.clone_url_ssh} {repo_dir}", shell=True, check=True)
    logger.debug(f"Repository cloned into {repo_dir}")
    return repo_dir

def perform_language_analysis(repo_dir, repo, session):
    """Run go-enry for language analysis."""
    logger.info(f"Performing language analysis for {repo.repo_name}")
    analysis_file = f"{repo_dir}/analysis.txt"
    subprocess.run(f"go-enry > {analysis_file}", shell=True, check=True)
    if not os.path.exists(analysis_file):
        raise FileNotFoundError("Language analysis file not found")
    with open(analysis_file, 'r') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                percent_usage, language = parts
                session.execute(
                    insert(LanguageAnalysis).values(
                        repo_id=repo.repo_id,
                        language=language,
                        percent_usage=float(percent_usage.strip('%'))
                    ).on_conflict_do_update(
                        index_elements=['repo_id', 'language'],
                        set_={'percent_usage': float(percent_usage.strip('%')), 'analysis_date': datetime.utcnow()}
                    )
                )
    session.commit()
    logger.debug(f"Language analysis completed for {repo.repo_name}")

def cleanup_repository_directory(repo_dir):
    """Clean up repository directory."""
    if os.path.exists(repo_dir):
        subprocess.run(f"rm -rf {repo_dir}", shell=True, check=True)
        logger.debug(f"Cleaned up repository directory: {repo_dir}")

def analyze_repositories(batch):
    """Process a batch of repositories."""
    session = Session()
    for repo in batch:
        try:
            set_repo_status(session, repo, "PROCESSING", "Starting processing")
            repo_dir = clone_repository(repo)
            perform_language_analysis(repo_dir, repo, session)
            set_repo_status(session, repo, "COMPLETED", "Processing completed successfully")
        except Exception as e:
            logger.error(f"Error processing repository {repo.repo_name}: {e}")
            set_repo_status(session, repo, "ERROR", str(e))
        finally:
            cleanup_repository_directory(repo_dir)
    session.close()

# Fetch Repositories
def fetch_repositories(batch_size=1000):
    session = Session()
    offset = 0
    while True:
        batch = session.query(Repository).filter_by(status="NEW").offset(offset).limit(batch_size).all()
        if not batch:
            break
        yield batch
        offset += batch_size
    session.close()

# DAG Definition
default_args = {'owner': 'airflow', 'start_date': datetime(2023, 12, 1), 'retries': 1}

with DAG(
    'repo_processing_with_batches',
    default_args=default_args,
    schedule_interval=None,
    max_active_tasks=10,
    catchup=False,
) as dag:

    def create_batches():
        batch_size = 1000
        num_tasks = 10
        all_repositories = [repo for batch in fetch_repositories(batch_size) for repo in batch]
        task_batches = [all_repositories[i::num_tasks] for i in range(num_tasks)]
        return task_batches

    batches = create_batches()

    for task_id, task_batch in enumerate(batches):
        PythonOperator(
            task_id=f"process_batch_{task_id}",
            python_callable=analyze_repositories,
            op_args=[task_batch],
        )
