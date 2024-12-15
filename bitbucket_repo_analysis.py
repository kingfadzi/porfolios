import logging
import re
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, Column, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import os
import subprocess

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database setup
DB_URL = "postgresql+psycopg2://username:password@localhost/repo_analysis"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Repository ORM model (read-only)
class Repository(Base):
    __tablename__ = "bitbucket_repositories"
    repo_id = Column(String, primary_key=True)
    project_key = Column(String)
    repo_name = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    clone_url_https = Column(String)
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

# Analyze a single repository and upsert results
def analyze_repo_task(repo_id):
    logger.debug(f"Starting analysis for repo_id: {repo_id}")
    session = Session()

    try:
        # Fetch repository details
        repo = session.query(Repository).filter(Repository.repo_id == repo_id).first()
        if not repo:
            logger.error(f"Repository with repo_id {repo_id} not found!")
            raise ValueError(f"Repository with repo_id {repo_id} not found!")
        logger.info(f"Fetched repository details: {repo.repo_name} ({repo.repo_id})")

        # Determine the clone URL
        clone_url = repo.clone_url_ssh or repo.clone_url_https
        if not clone_url:
            logger.error(f"No clone URL for repository {repo.repo_name} (ID: {repo.repo_id})")
            raise ValueError(f"No clone URL for repository {repo.repo_name} (ID: {repo.repo_id})")
        logger.debug(f"Using clone URL: {clone_url}")

        # Clone the repository
        repo_dir = f"/tmp/{repo.repo_slug}"
        os.system(f"git clone {clone_url} {repo_dir}")
        logger.info(f"Cloned repository {repo.repo_name} to {repo_dir}")

        # Run go-enry analysis
        analysis_file = f"{repo_dir}_analysis.txt"
        subprocess.run(f"go-enry {repo_dir} > {analysis_file}", shell=True, check=True)
        logger.info(f"go-enry analysis completed. Output saved to {analysis_file}")

        # Parse go-enry output
        with open(analysis_file, 'r') as f:
            lines = f.readlines()
        results = [line.strip().split(',') for line in lines]
        logger.debug(f"Parsed go-enry results: {results}")

        # Perform upsert into the languages_analysis table
        for language, percent_usage in results:
            stmt = insert(LanguageAnalysis).values(
                repo_id=repo.repo_id,
                language=language,
                percent_usage=float(percent_usage)
            ).on_conflict_do_update(
                index_elements=['repo_id', 'language'],
                set_={
                    'percent_usage': float(percent_usage),
                    'analysis_date': datetime.utcnow()
                }
            )
            session.execute(stmt)
        session.commit()
        logger.info(f"Analysis results upserted for repository {repo.repo_name} ({repo.repo_id})")

    except Exception as e:
        logger.exception(f"Error processing repository {repo_id}: {e}")
        session.rollback()
        raise e

    finally:
        os.system(f"rm -rf {repo_dir}")
        session.close()

# Fetch a sample of 10 repositories
def fetch_sample_repositories():
    """Fetch a sample of 10 repositories from the bitbucket_repositories table."""
    logger.debug("Fetching a sample of 10 repositories.")
    session = Session()
    try:
        return session.query(Repository).limit(10).all()
    finally:
        session.close()

# Sanitize task IDs
def sanitize_task_id(task_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", task_id)

# Define the Airflow DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 15),
    'retries': 1,
}

with DAG('bitbucket_repo_analysis_sample', default_args=default_args, schedule_interval=None) as dag:
    # Fetch a sample of 10 repositories and create tasks
    repositories = fetch_sample_repositories()

    for repo in repositories:
        sanitized_task_id = sanitize_task_id(f"analyze_repo_{repo.repo_id}")
        analyze_task = PythonOperator(
            task_id=sanitized_task_id,
            python_callable=analyze_repo_task,
            op_kwargs={'repo_id': repo.repo_id},
        )
