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
    while True:
        batch = session.query(Repository).offset(offset).limit(batch_size).all()
        if not batch:
            break
        yield batch
        offset += batch_size
    session.close()

# Ensure SSH URL
def ensure_ssh_url(clone_url):
    if clone_url.startswith("https://"):
        match = re.match(r"https://(.*?)/scm/(.*?)/(.*?\.git)", clone_url)
        if match:
            domain, project_key, repo_slug = match.groups()
            return f"ssh://git@{domain}:7999/{project_key}/{repo_slug}"
    elif clone_url.startswith("ssh://"):
        return clone_url
    raise ValueError(f"Unsupported URL format: {clone_url}")

# Analyze repositories
def analyze_repositories(batch):
    session = Session()
    for repo in batch:
        try:
            if not isinstance(repo, Repository):
                logger.error(f"Invalid repository object: {repo}")
                continue

            clone_url = ensure_ssh_url(repo.clone_url_ssh)
            repo_dir = f"/tmp/{repo.repo_slug}"
            subprocess.run(f"git clone {clone_url} {repo_dir}", shell=True, check=True)
            analysis_file = f"{repo_dir}_analysis.txt"
            subprocess.run(f"go-enry {repo_dir} > {analysis_file}", shell=True, check=True)

            if os.path.exists(analysis_file):
                with open(analysis_file, 'r') as f:
                    lines = f.readlines()
                results = [line.strip().split(',') for line in lines if line.strip()]

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
            os.system(f"rm -rf {repo_dir}")
        except Exception as e:
            logger.error(f"Error processing repository {repo.repo_name}: {e}")
            session.rollback()
        finally:
            session.close()

# DAG definition
default_args = {'owner': 'airflow', 'depends_on_past': False, 'start_date': datetime(2023, 12, 15), 'retries': 1}

with DAG(
    'repo_processing_with_batches',
    default_args=default_args,
    schedule_interval=None,
    max_active_tasks=10,
) as dag:

    # Fetch repositories and dynamically create tasks
    def create_and_process_batches():
        batch_size = 1000
        num_tasks = 10

        # Flatten all repositories into a single list
        all_repositories = [repo for batch in fetch_repositories(batch_size) for repo in batch]

        # Split the flat list into task batches
        task_batches = [all_repositories[i::num_tasks] for i in range(num_tasks)]

        # Dynamically create tasks for each batch
        for task_id, task_batch in enumerate(task_batches):
            PythonOperator(
                task_id=f"process_batch_{task_id}",
                python_callable=analyze_repositories,
                op_args=[task_batch],
                dag=dag,  # Ensure the dynamically created task is attached to the DAG
            )

    # Create the dynamic tasks
    create_batches_task = PythonOperator(
        task_id="create_batches_and_tasks",
        python_callable=create_and_process_batches,
    )
