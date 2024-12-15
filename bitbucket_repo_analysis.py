import logging
import os
import re
import subprocess
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, Column, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_URL = "postgresql+psycopg2://postgres:postgres@localhost/gitlab-usage"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Repository ORM model
class Repository(Base):
    __tablename__ = "bitbucket_repositories"
    repo_id = Column(String, primary_key=True)
    project_key = Column(String)
    repo_name = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    clone_url_ssh = Column(String)
    language = Column(String)
    size = Column(Float)
    forks = Column(Float)
    created_on = Column(DateTime)
    updated_on = Column(DateTime)

# Languages Analysis ORM model
class LanguageAnalysis(Base):
    __tablename__ = "languages_analysis"
    id = Column(String, primary_key=True)
    repo_id = Column(String, nullable=False)
    language = Column(String, nullable=False)
    percent_usage = Column(Float, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('repo_id', 'language', name='_repo_language_uc'),)

# Fetch repositories in batches
def fetch_repositories_in_batches(batch_size=1000):
    """
    Generator to fetch repositories in batches.
    This avoids loading all records into memory at once.
    """
    session = Session()
    offset = 0

    while True:
        batch = session.query(Repository).offset(offset).limit(batch_size).all()
        if not batch:
            break
        yield batch
        offset += batch_size

    session.close()

# Ensure the URL is in SSH format
def ensure_ssh_url(clone_url):
    """
    Ensure the given URL is in SSH format.
    If the URL is HTTP, convert it to SSH.
    """
    if clone_url.startswith("https://"):
        match = re.match(r"https://(.*?)/scm/(.*?)/(.*?\.git)", clone_url)
        if not match:
            raise ValueError(f"Invalid HTTP URL format: {clone_url}")
        domain, project_key, repo_slug = match.groups()
        ssh_url = f"ssh://git@{domain}:7999/{project_key}/{repo_slug}"
        return ssh_url
    elif clone_url.startswith("ssh://"):
        return clone_url
    else:
        raise ValueError(f"Unsupported URL format: {clone_url}")

# Analyze a single repository
def analyze_repo_task(repo_id):
    logger.info(f"Processing repository with ID: {repo_id}")
    session = Session()
    try:
        # Fetch repository details
        repo = session.query(Repository).filter(Repository.repo_id == repo_id).first()
        if not repo:
            logger.error(f"Repository with ID {repo_id} not found!")
            raise ValueError(f"Repository with ID {repo_id} not found!")

        logger.info(f"Fetched repository: {repo.repo_name} ({repo.repo_id})")
        clone_url = ensure_ssh_url(repo.clone_url_ssh)

        # Clone the repository
        repo_dir = f"/tmp/{repo.repo_slug}"
        logger.info(f"Cloning repository: {clone_url} into {repo_dir}")
        subprocess.run(f"git clone {clone_url} {repo_dir}", shell=True, check=True)

        # Run go-enry analysis
        analysis_file = f"{repo_dir}_analysis.txt"
        go_enry_cmd = f"go-enry {repo_dir} > {analysis_file}"
        logger.info(f"Running go-enry analysis: {go_enry_cmd}")
        subprocess.run(go_enry_cmd, shell=True, check=True)

        # Parse and upsert analysis results
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                lines = f.readlines()
            results = [line.strip().split(',') for line in lines if line.strip()]

            logger.info(f"Parsed go-enry results for {repo.repo_name}: {results}")
            for language, percent_usage in results:
                stmt = insert(LanguageAnalysis).values(
                    repo_id=repo.repo_id,
                    language=language,
                    percent_usage=float(percent_usage),
                ).on_conflict_do_update(
                    index_elements=['repo_id', 'language'],
                    set_={
                        'percent_usage': float(percent_usage),
                        'analysis_date': datetime.utcnow(),
                    },
                )
                session.execute(stmt)
            session.commit()
        else:
            logger.error(f"Analysis file not found for {repo.repo_name}")

        # Cleanup
        os.system(f"rm -rf {repo_dir}")

    except Exception as e:
        logger.error(f"Error processing repository {repo_id}: {e}")
        raise e

    finally:
        session.close()

# Sanitize task IDs
def sanitize_task_id(task_id: str) -> str:
    """
    Ensure task IDs are alphanumeric and meet Airflow's requirements.
    Replaces invalid characters with underscores.
    """
    sanitized_id = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", task_id)
    if len(sanitized_id) > 200:
        sanitized_id = sanitized_id[:200]  # Ensure task ID is within Airflow's character limit
    return sanitized_id

# Define the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 15),
    'retries': 1,
}

with DAG(
    'repo_processing_with_language_update',
    default_args=default_args,
    schedule_interval=None,
    max_active_tasks=16,  # Adjust based on system resources
) as dag:
    batch_size = 1000
    for batch in fetch_repositories_in_batches(batch_size=batch_size):
        for repo in batch:
            task_id = sanitize_task_id(f"analyze_repo_{repo.repo_id}")
            PythonOperator(
                task_id=task_id,
                python_callable=analyze_repo_task,
                op_kwargs={'repo_id': repo.repo_id},
            )
