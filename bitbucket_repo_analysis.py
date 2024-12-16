import logging
import os
import re
import subprocess
from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from git import Repo, InvalidGitRepositoryError, GitCommandError
import pytz

# Set up logging
logging.basicConfig(level=logging.DEBUG)
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

class RepoMetrics(Base):
    __tablename__ = "repo_metrics"
    repo_id = Column(String, primary_key=True)
    repo_size_bytes = Column(Float, nullable=False)
    file_count = Column(Integer, nullable=False)
    total_commits = Column(Integer, nullable=False)
    number_of_contributors = Column(Integer, nullable=False)
    last_commit_date = Column(DateTime, nullable=True)
    repo_age_days = Column(Integer, nullable=False)
    active_branch_count = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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

def get_default_branch(repo_obj):
    """
    Detect the default branch for a repository.
    """
    try:
        # Try to get the active branch
        return repo_obj.active_branch.name
    except (TypeError, AttributeError):
        # If no active branch, check common defaults or fall back
        logger.warning("No active branch detected. Attempting to guess the default branch.")
        branches = [head.name for head in repo_obj.heads]
        if "main" in branches:
            return "main"
        elif branches:
            return branches[0]  # Fallback to the first branch
        else:
            raise ValueError("Repository has no branches.")

# Analyze repositories
def analyze_repositories(batch):
    logger.info(f"Processing a batch of {len(batch)} repositories.")
    session = Session()
    for repo in batch:
        try:
            logger.info(f"Processing repository: {repo.repo_name} (ID: {repo.repo_id})")

            # Ensure clone URL
            clone_url = ensure_ssh_url(repo.clone_url_ssh)

            # Clone the repository
            repo_dir = f"/tmp/{repo.repo_slug}"
            logger.info(f"Cloning repository {repo.repo_name} into {repo_dir}")
            subprocess.run(f"git clone {clone_url} {repo_dir}", shell=True, check=True)

            # Change working directory to repo_dir and run go-enry
            logger.info(f"Changing working directory to {repo_dir} for go-enry analysis.")
            original_dir = os.getcwd()
            os.chdir(repo_dir)

            try:
                # Language Analysis
                logger.info(f"Running go-enry in directory: {os.getcwd()}")
                analysis_file = f"{repo_dir}/analysis.txt"
                go_enry_command = f"go-enry > {analysis_file}"
                subprocess.run(go_enry_command, shell=True, check=True)

                if os.path.exists(analysis_file):
                    logger.info(f"Analysis file found: {analysis_file}")
                    with open(analysis_file, 'r') as f:
                        lines = f.readlines()

                    # Parse and save language analysis
                    results = []
                    for line in lines:
                        parts = line.strip().split(maxsplit=1)
                        if len(parts) == 2:
                            percent_usage, language = parts
                            results.append((language.strip(), float(percent_usage.strip('%'))))

                    for language, percent_usage in results:
                        stmt = insert(LanguageAnalysis).values(
                            repo_id=repo.repo_id,
                            language=language,
                            percent_usage=percent_usage,
                        ).on_conflict_do_update(
                            index_elements=['repo_id', 'language'],
                            set_={'percent_usage': percent_usage, 'analysis_date': datetime.utcnow()},
                        )
                        session.execute(stmt)
                    session.commit()

                # Repository Metrics Analysis
                calculate_and_persist_repo_metrics(repo_dir, repo, session)

            finally:
                # Reset working directory
                os.chdir(original_dir)

        except Exception as e:
            logger.error(f"Error processing repository {repo.repo_name}: {e}")
            session.rollback()
        finally:
            # Cleanup
            if os.path.exists(repo_dir):
                subprocess.run(f"rm -rf {repo_dir}", shell=True)
    session.close()

def calculate_and_persist_repo_metrics(repo_dir, repo, session):
    try:
        logger.info(f"Calculating repository metrics for {repo.repo_name} (ID: {repo.repo_id})")
        repo_obj = Repo(repo_dir)

        # Get the default branch
        default_branch = get_default_branch(repo_obj)
        logger.info(f"Default branch detected: {default_branch}")

        # Calculate repository metrics
        total_size = sum(blob.size for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
        file_count = sum(1 for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
        total_commits = sum(1 for _ in repo_obj.iter_commits(default_branch))
        contributors = set(commit.author.email for commit in repo_obj.iter_commits(default_branch))
        last_commit_date = max(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
        first_commit_date = min(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
        repo_age_days = (datetime.now(pytz.utc) - first_commit_date).days
        active_branch_count = sum(
            1 for branch in repo_obj.branches
            if (datetime.now(pytz.utc) - repo_obj.commit(branch.name).committed_datetime).days <= 90
        )

        # Upsert repository metrics into the database
        stmt = insert(RepoMetrics).values(
            repo_id=repo.repo_id,
            repo_size_bytes=total_size,
            file_count=file_count,
            total_commits=total_commits,
            number_of_contributors=len(contributors),
            last_commit_date=last_commit_date,
            repo_age_days=repo_age_days,
            active_branch_count=active_branch_count
        ).on_conflict_do_update(
            index_elements=['repo_id'],
            set_={
                "repo_size_bytes": total_size,
                "file_count": file_count,
                "total_commits": total_commits,
                "number_of_contributors": len(contributors),
                "last_commit_date": last_commit_date,
                "repo_age_days": repo_age_days,
                "active_branch_count": active_branch_count,
                "updated_at": datetime.utcnow()
            }
        )
        session.execute(stmt)
        session.commit()
        logger.info(f"Repository metrics saved for {repo.repo_name} (ID: {repo.repo_id})")
    except Exception as e:
        logger.error(f"Error calculating repository metrics for {repo.repo_name}: {e}")
        session.rollback()

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
