from airflow import DAG
from airflow.decorators import task
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import gitlab
import hashlib
import logging
from urllib.parse import quote

# Configuration
GITLAB_URL = "https://gitlab.example.com"
PRIVATE_TOKEN = "your_private_token"
DB_CONNECTION = "postgresql+psycopg2://user:password@localhost/dbname"
INPUT_FILE = "/path/to/input_projects.csv"
N_DAYS = 7  # Number of days to look back for metrics
BATCH_SIZE = 100  # Number of projects to process per batch

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize GitLab client
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

# SQLAlchemy Base and ORM Models
Base = declarative_base()

class InputProject(Base):
    __tablename__ = "input_projects"
    id = Column(String, primary_key=True)  # SHA256 hash of the URL
    gitlab_project_url = Column(String, unique=True, nullable=False)
    lob = Column(String)
    dpt = Column(String)
    project_name = Column(String)
    appid = Column(String)
    appname = Column(String)
    gitlab_workspace = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProjectMetric(Base):
    __tablename__ = "project_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    input_project_id = Column(String)  # Foreign key to InputProject.id
    commit_count = Column(Integer)
    contributor_count = Column(Integer)
    branch_count = Column(Integer)
    last_commit_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProjectLanguage(Base):
    __tablename__ = "project_languages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_metric_id = Column(Integer)  # Foreign key to ProjectMetric.id
    language_name = Column(String)
    percentage = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize SQLAlchemy
engine = create_engine(DB_CONNECTION)
Session = sessionmaker(bind=engine)

# Hashing Function
def generate_hash(url):
    """Generate a SHA256 hash for the given URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

@task
def load_csv_to_db():
    """Load CSV into input_projects table using hashed IDs."""
    session = Session()
    try:
        df = pd.read_csv(INPUT_FILE)
        projects = []
        for _, row in df.iterrows():
            url = row["gitlab_project_url"].strip()
            url_hash = generate_hash(url)

            project = InputProject(
                id=url_hash,
                gitlab_project_url=url,
                lob=row["LOB"],
                dpt=row["dpt"],
                project_name=row["project_name"],
                appid=row["appid"],
                appname=row["appname"],
                gitlab_workspace=row["gitlab_workspace"],
            )
            projects.append(project)

        # Perform a bulk insert
        session.bulk_save_objects(projects, return_defaults=False)
        session.commit()
        logger.info(f"Successfully loaded {len(projects)} rows into input_projects.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error loading CSV: {e}")
        raise
    finally:
        session.close()

def fetch_batch(session, model, batch_number, batch_size=BATCH_SIZE):
    """Fetch a batch of rows from the database."""
    return session.query(model).offset(batch_number * batch_size).limit(batch_size).all()

@task
def fetch_metrics(batch_number):
    """Fetch metrics for a batch of projects."""
    session = Session()
    try:
        projects = fetch_batch(session, InputProject, batch_number, batch_size=BATCH_SIZE)
        if not projects:
            logger.info(f"No projects found in batch {batch_number}.")
            return

        for project in projects:
            logger.info(f"Fetching metrics for project: {project.gitlab_project_url} (Hash: {project.id})")

            # Fetch project details from GitLab
            parsed_url = quote(project.gitlab_project_url.strip('/'), safe='')
            gl_project = gl.http_get(f"/projects/{parsed_url}")
            gitlab_project_id = gl_project["id"]

            project_obj = gl.projects.get(gitlab_project_id)
            commits = project_obj.commits.list(since=(datetime.utcnow() - timedelta(days=N_DAYS)).isoformat() + "Z")
            commit_count = len(commits)
            contributors = len({commit.author_email for commit in commits})
            branches = len(project_obj.branches.list())
            last_commit_date = max(commit.created_at for commit in commits)

            # Upsert metrics
            metric = session.query(ProjectMetric).filter_by(input_project_id=project.id).first()
            if not metric:
                metric = ProjectMetric(
                    input_project_id=project.id,
                    commit_count=commit_count,
                    contributor_count=contributors,
                    branch_count=branches,
                    last_commit_date=last_commit_date,
                )
                session.add(metric)
            else:
                metric.commit_count = commit_count
                metric.contributor_count = contributors
                metric.branch_count = branches
                metric.last_commit_date = last_commit_date
            session.commit()
    finally:
        session.close()

@task
def fetch_languages(batch_number):
    """Fetch languages for a batch of projects."""
    session = Session()
    try:
        metrics = fetch_batch(session, ProjectMetric, batch_number, batch_size=BATCH_SIZE)
        if not metrics:
            logger.info(f"No metrics found in batch {batch_number}.")
            return

        for metric in metrics:
            logger.info(f"Fetching languages for project_metric_id: {metric.id}")

            project_obj = gl.projects.get(metric.id)
            languages = project_obj.languages()

            # Clear old languages
            session.query(ProjectLanguage).filter_by(project_metric_id=metric.id).delete()

            # Insert new languages
            for language, percentage in languages.items():
                session.add(ProjectLanguage(project_metric_id=metric.id, language_name=language, percentage=percentage))
            session.commit()
    finally:
        session.close()

# Define DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="software_repo_analysis_batches",
    default_args=default_args,
    description="Analyze GitLab repositories with batched tasks",
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    max_active_tasks=10,  # Limit concurrent tasks
) as dag:

    load_csv = load_csv_to_db()

    # Parallel metrics processing
    with TaskGroup("fetch_metrics_group") as fetch_metrics_group:
        for batch_num in range(10):  # Number of batches (adjust as needed)
            fetch_metrics(batch_number=batch_num)

    # Parallel languages processing
    with TaskGroup("fetch_languages_group") as fetch_languages_group:
        for batch_num in range(10):  # Number of batches (adjust as needed)
            fetch_languages(batch_number=batch_num)

    # Define task dependencies
    load_csv >> fetch_metrics_group >> fetch_languages_group
