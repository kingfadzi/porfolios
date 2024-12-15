import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, Column, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import os
import subprocess
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
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

# Languages Analysis ORM model (managed by this script)
class LanguageAnalysis(Base):
    __tablename__ = "languages_analysis"
    id = Column(String, primary_key=True)
    repo_id = Column(String, nullable=False)
    language = Column(String, nullable=False)
    percent_usage = Column(Float, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('repo_id', 'language', name='_repo_language_uc'),)

# Ensure the languages_analysis table is created
def initialize_languages_table():
    logger.debug("Initializing languages_analysis table.")
    Base.metadata.create_all(engine)
    logger.info("languages_analysis table created (if not already existing).")

# Analyze a repository and upsert into languages_analysis
def analyze_repo(repo_id, **kwargs):
    session = Session()
    logger.debug(f"Starting analysis for repo_id: {repo_id}")

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
            logger.error(f"No clone URL found for repository {repo.repo_name} (ID: {repo.repo_id})")
            raise ValueError(f"No clone URL found for repository {repo.repo_name} (ID: {repo.repo_id})")
        logger.debug(f"Using clone URL: {clone_url}")

        # Clone the repository
        repo_dir = f"/tmp/{repo.repo_slug}"
        logger.debug(f"Cloning repository to {repo_dir}")
        os.system(f"git clone {clone_url} {repo_dir}")
        logger.info(f"Cloned repository {repo.repo_name} to {repo_dir}")

        # Run go-enry analysis
        analysis_file = f"{repo_dir}_analysis.txt"
        logger.debug(f"Running go-enry analysis on {repo_dir}")
        subprocess.run(f"go-enry {repo_dir} > {analysis_file}", shell=True, check=True)
        logger.info(f"go-enry analysis completed. Output saved to {analysis_file}")

        # Parse go-enry output
        with open(analysis_file, 'r') as f:
            lines = f.readlines()
        results = [line.strip().split(',') for line in lines]
        logger.debug(f"Parsed go-enry results: {results}")

        # Perform upsert into the languages_analysis table
        for language, percent_usage in results:
            logger.debug(f"Upserting language: {language}, usage: {percent_usage}%")
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
        logger.info(f"Analysis results upserted for repository {repo.repo_name} ({repo.repo_id})")

        # Commit results
        session.commit()

    except Exception as e:
        logger.exception(f"Error processing repository {repo_id}: {e}")
        session.rollback()
        raise e

    finally:
        # Clean up temporary files
        logger.debug(f"Cleaning up temporary files for {repo.repo_name} ({repo.repo_id})")
        os.system(f"rm -rf {repo_dir}")
        session.close()

# Sanitize task IDs
def sanitize_task_id(task_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", task_id)

# Airflow DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 15),
    'retries': 1,
}

with DAG('bitbucket_repo_analysis', default_args=default_args, schedule_interval=None, concurrency=20) as dag:
    # Ensure the languages_analysis table exists
    initialize_task = PythonOperator(
        task_id='initialize_languages_table',
        python_callable=initialize_languages_table
    )

    session = Session()
    repositories = session.query(Repository).all()
    session.close()

    analyze_tasks = []
    for repo in repositories:
        # Sanitize task ID
        sanitized_task_id = sanitize_task_id(f"analyze_repo_{repo.repo_id}")

        analyze_task = PythonOperator(
            task_id=sanitized_task_id,
            python_callable=analyze_repo,
            op_kwargs={'repo_id': repo.repo_id},
        )
        initialize_task >> analyze_task  # Ensure initialization happens first
        analyze_tasks.append(analyze_task)
