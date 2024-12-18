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
def ensure_ssh_url(clone_url):
    """Convert HTTPS clone URLs to SSH format."""
    if clone_url.startswith("https://"):
        match = re.match(r"https://(.*?)/scm/(.*?)/(.*?\.git)", clone_url)
        if match:
            domain, project_key, repo_slug = match.groups()
            return f"ssh://git@{domain}:7999/{project_key}/{repo_slug}"
    elif clone_url.startswith("ssh://"):
        return clone_url
    raise ValueError(f"Unsupported URL format: {clone_url}")

def clone_repository(repo):
    """Ensure SSH URL format and clone the repository."""
    logger.info(f"Cloning repository {repo.repo_name}...")
    base_dir = "/mnt/tmpfs/cloned_repositories"
    repo_dir = f"{base_dir}/{repo.repo_slug}"
    os.makedirs(base_dir, exist_ok=True)
    clone_url = ensure_ssh_url(repo.clone_url_ssh)
    logger.debug(f"Using clone URL: {clone_url}")
    subprocess.run(f"rm -rf {repo_dir} && git clone {clone_url} {repo_dir}", shell=True, check=True)
    logger.info(f"Repository cloned successfully into {repo_dir}.")
    return repo_dir

def perform_language_analysis(repo_dir, repo, session):
    """Run go-enry for language analysis."""
    logger.info(f"Starting language analysis for repository {repo.repo_name}.")
    analysis_file = f"{repo_dir}/analysis.txt"
    subprocess.run(f"go-enry > {analysis_file}", shell=True, check=True)
    if not os.path.exists(analysis_file):
        logger.error("Language analysis file not found.")
        raise FileNotFoundError("Language analysis file not found.")
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
    logger.info(f"Language analysis completed successfully for repository {repo.repo_name}.")

def calculate_and_persist_repo_metrics(repo_dir, repo, session):
    """Calculate and persist repository metrics."""
    logger.info(f"Calculating repository metrics for {repo.repo_name}.")
    repo_obj = Repo(repo_dir)
    default_branch = repo_obj.active_branch.name
    logger.debug(f"Default branch detected: {default_branch}")

    total_size = sum(blob.size for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    file_count = sum(1 for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    total_commits = sum(1 for _ in repo_obj.iter_commits(default_branch))
    contributors = set(commit.author.email for commit in repo_obj.iter_commits(default_branch))
    last_commit_date = max(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    first_commit_date = min(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    repo_age_days = (datetime.utcnow().replace(tzinfo=pytz.utc) - first_commit_date).days

    logger.debug(f"Metrics calculated: size={total_size}, file_count={file_count}, commits={total_commits}, contributors={len(contributors)}.")
    session.execute(
        insert(RepoMetrics).values(
            repo_id=repo.repo_id,
            repo_size_bytes=total_size,
            file_count=file_count,
            total_commits=total_commits,
            number_of_contributors=len(contributors),
            last_commit_date=last_commit_date,
            repo_age_days=repo_age_days,
            active_branch_count=len(repo_obj.branches)
        ).on_conflict_do_update(
            index_elements=['repo_id'],
            set_={"repo_size_bytes": total_size, "file_count": file_count, "updated_at": datetime.utcnow()}
        )
    )
    session.commit()
    logger.info(f"Metrics saved for repository {repo.repo_name}.")

def cleanup_repository_directory(repo_dir):
    """Remove the repository directory."""
    if os.path.exists(repo_dir):
        subprocess.run(f"rm -rf {repo_dir}", shell=True, check=True)
        logger.info(f"Cleaned up repository directory: {repo_dir}.")

def analyze_repositories(batch):
    """Process a batch of repositories."""
    session = Session()
    for repo in batch:
        try:
            logger.info(f"Starting processing for repository {repo.repo_name} (ID: {repo.repo_id}). Current status: {repo.status}")

            # Set status to PROCESSING
            repo.status = "PROCESSING"
            repo.comment = "Starting processing."
            repo.updated_on = datetime.utcnow()

            # Add the repo to the session for tracking changes
            session.add(repo)
            session.commit()

            logger.info(f"Updated repository {repo.repo_name} (ID: {repo.repo_id}) to PROCESSING. Comment: {repo.comment}")

            # Clone the repository
            repo_dir = clone_repository(repo)

            # Perform language analysis
            perform_language_analysis(repo_dir, repo, session)

            # Calculate repository metrics
            calculate_and_persist_repo_metrics(repo_dir, repo, session)

            # Set status to COMPLETED
            repo.status = "COMPLETED"
            repo.comment = "Processing completed successfully."
            repo.updated_on = datetime.utcnow()

            # Commit changes
            session.add(repo)
            session.commit()

            logger.info(f"Updated repository {repo.repo_name} (ID: {repo.repo_id}) to COMPLETED. Comment: {repo.comment}")
        except Exception as e:
            logger.error(f"Error processing repository {repo.repo_name} (ID: {repo.repo_id}): {e}")
            repo.status = "ERROR"
            repo.comment = str(e)
            repo.updated_on = datetime.utcnow()

            # Commit changes
            session.add(repo)
            session.commit()

            logger.info(f"Updated repository {repo.repo_name} (ID: {repo.repo_id}) to ERROR. Comment: {repo.comment}")
        finally:
            cleanup_repository_directory(repo_dir)

    # Close the session after processing the batch
    session.close()


# Fetch Repositories
def fetch_repositories(batch_size=1000):
    """Fetch repositories in batches of a given size."""
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
        logger.info("Fetching repositories and creating batches.")
        all_repositories = [repo for batch in fetch_repositories(batch_size) for repo in batch]
        task_batches = [all_repositories[i::num_tasks] for i in range(num_tasks)]
        logger.info(f"Created {len(task_batches)} batches for processing.")
        return task_batches

    batches = create_batches()

    for task_id, batch in enumerate(batches):
        PythonOperator(
            task_id=f"process_batch_{task_id}",
            python_callable=analyze_repositories,
            op_args=[batch],
        )
