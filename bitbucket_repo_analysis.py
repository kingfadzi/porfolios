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
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed messages
logger = logging.getLogger(__name__)

# Database setup
DB_URL = "postgresql+psycopg2://postgres:postgres@localhost/gitlab-usage"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ORM models
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

class LanguageAnalysis(Base):
    __tablename__ = "languages_analysis"
    id = Column(String, primary_key=True)
    repo_id = Column(String, nullable=False)
    language = Column(String, nullable=False)
    percent_usage = Column(Float, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('repo_id', 'language', name='_repo_language_uc'),)

# Fetch repositories
def fetch_repositories(batch_size=1000):
    session = Session()
    offset = 0
    logger.debug(f"Starting to fetch repositories in batches of {batch_size}")
    while True:
        batch = session.query(Repository).offset(offset).limit(batch_size).all()
        if not batch:
            logger.debug("No more repositories to fetch.")
            break
        logger.debug(f"Fetched {len(batch)} repositories from offset {offset}")
        yield batch
        offset += batch_size
    session.close()
    logger.debug("Completed fetching all repositories.")

# Ensure SSH URL
def ensure_ssh_url(clone_url):
    logger.debug(f"Ensuring SSH format for URL: {clone_url}")
    if clone_url.startswith("https://"):
        match = re.match(r"https://(.*?)/scm/(.*?)/(.*?\.git)", clone_url)
        if match:
            domain, project_key, repo_slug = match.groups()
            ssh_url = f"ssh://git@{domain}:7999/{project_key}/{repo_slug}"
            logger.debug(f"Converted HTTPS URL to SSH: {ssh_url}")
            return ssh_url
    elif clone_url.startswith("ssh://"):
        logger.debug(f"URL is already in SSH format: {clone_url}")
        return clone_url
    else:
        logger.error(f"Unsupported URL format: {clone_url}")
        raise ValueError(f"Unsupported URL format: {clone_url}")

# Analyze repositories
def analyze_repositories(batch):
    logger.info(f"Processing a batch of {len(batch)} repositories.")
    session = Session()
    for repo in batch:
        try:
            logger.info(f"Processing repository: {repo.repo_name} (ID: {repo.repo_id})")
            logger.debug(f"Repository details: {repo}")

            # Ensure clone URL
            clone_url = ensure_ssh_url(repo.clone_url_ssh)

            # Clone the repository
            repo_dir = f"/tmp/{repo.repo_slug}"
            logger.info(f"Cloning repository {repo.repo_name} into {repo_dir}")
            subprocess.run(f"git clone {clone_url} {repo_dir}", shell=True, check=True)

            # Run go-enry
            analysis_file = f"{repo_dir}_analysis.txt"
            go_enry_command = f"go-enry {repo_dir} > {analysis_file}"
            logger.info(f"Running go-enry analysis: {go_enry_command}")
            subprocess.run(go_enry_command, shell=True, check=True)

            # Parse and log results
            if os.path.exists(analysis_file):
                logger.info(f"Analysis file found: {analysis_file}")
                with open(analysis_file, 'r') as f:
                    lines = f.readlines()
                if lines:
                    logger.debug(f"Content of analysis file for {repo.repo_name}:\n{''.join(lines)}")
                else:
                    logger.warning(f"Analysis file is empty for {repo.repo_name}")
                results = [line.strip().split(',') for line in lines if line.strip()]
                logger.debug(f"Parsed go-enry results: {results}")

                # Upsert results into the database
                for language, percent_usage in results:
                    stmt = insert(LanguageAnalysis).values(
                        repo_id=repo.repo_id,
                        language=language,
                        percent_usage=float(percent_usage),
                    ).on_conflict_do_update(
                        index_elements=['repo_id', 'language'],
                        set_={'percent_usage': float(percent_usage), 'analysis_date': datetime.utcnow()},
                    )
                    session.execute(stmt)
                session.commit()
                logger.info(f"Language analysis results saved for repository {repo.repo_name}")
            else:
                logger.error(f"Analysis file not found for repository {repo.repo_name}")

            # Cleanup
            logger.info(f"Deleting cloned repository directory: {repo_dir}")
            if os.system(f"rm -rf {repo_dir}") == 0:
                logger.info(f"Successfully deleted {repo_dir}")
            else:
                logger.error(f"Failed to delete {repo_dir}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error: {e}")
        except Exception as e:
            logger.error(f"Error processing repository {repo.repo_name if repo else 'unknown'}: {e}")
            session.rollback()
        finally:
            session.close()

# DAG definition
default_args = {'owner': 'airflow', 'depends_on_past': False, 'start_date': datetime(2023, 12, 15), 'retries': 1}

with DAG(
    'repo_processing_with_batches_debug',
    default_args=default_args,
    schedule_interval=None,
    max_active_tasks=10,
) as dag:

    # Task 1: Create batches task
    def create_batches():
        batch_size = 1000
        num_tasks = 10
        logger.info("Starting batch creation process.")
        # Flatten all repositories into a single list
        all_repositories = [repo for batch in fetch_repositories(batch_size) for repo in batch]
        logger.info(f"Fetched {len(all_repositories)} repositories in total.")

        # Split the flat list into task batches
        task_batches = [all_repositories[i::num_tasks] for i in range(num_tasks)]
        logger.info(f"Created {num_tasks} task batches.")
        return task_batches

    batches = create_batches()  # Generate batches at DAG parse time

    # Dynamically create and register tasks
    for task_id, task_batch in enumerate(batches):
        process_batch_task = PythonOperator(
            task_id=f"process_batch_{task_id}",
            python_callable=analyze_repositories,
            op_args=[task_batch],
        )
