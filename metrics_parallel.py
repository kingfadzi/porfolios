from airflow import DAG
from airflow.decorators import task, dag
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
import gitlab
import pandas as pd
import logging
from urllib.parse import quote
import hashlib

# Configuration
GITLAB_URL = "https://gitlab.example.com"
PRIVATE_TOKEN = "your_private_token"
DB_NAME = "your_db_name"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_HOST = "localhost"
DB_PORT = 5432
INPUT_FILE = "/path/to/input_projects.csv"
N_DAYS = 7  # Number of days to look back for metrics

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# SQLAlchemy Base and ORM Models
Base = declarative_base()

class InputProject(Base):
    __tablename__ = "input_projects"
    id = Column(String, primary_key=True)  # Hash of the URL
    gitlab_project_url = Column(String, unique=True)
    lob = Column(String)
    dpt = Column(String)
    project_name = Column(String)
    appid = Column(String)
    appname = Column(String)
    gitlab_workspace = Column(String)

class ProjectMetric(Base):
    __tablename__ = "project_metrics"
    id = Column(Integer, primary_key=True)  # GitLab Project ID
    input_id = Column(String)  # Foreign Key to InputProject.id
    commit_count = Column(Integer)
    contributor_count = Column(Integer)
    branch_count = Column(Integer)
    last_commit_date = Column(DateTime)

class ProjectLanguage(Base):
    __tablename__ = "project_languages"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer)  # Foreign key to ProjectMetric.id
    language = Column(String)  # Language name
    percentage = Column(String)  # Percentage as text

# Initialize GitLab client
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

# Create database engine and session
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

def generate_hash(url):
    """Generate a hash for the given URL."""
    return hashlib.sha256(url.encode()).hexdigest()

@task
def load_csv_row(row):
    """Load a single row from the CSV into the `input_projects` table."""
    try:
        url = row["gitlab_project_url"].strip()
        url_hash = generate_hash(url)
        logger.info(f"Loading row for project: {url} (Hash: {url_hash})")

        record = InputProject(
            id=url_hash,
            gitlab_project_url=url,
            lob=row["LOB"],
            dpt=row["dpt"],
            project_name=row["project_name"],
            appid=row["appid"],
            appname=row["appname"],
            gitlab_workspace=row["gitlab_workspace"]
        )
        session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error loading row: {e}")
        raise

@task
def process_metrics_row(project):
    """Process metrics for a single project."""
    try:
        project_url = project.gitlab_project_url
        url_hash = project.id
        logger.info(f"Processing metrics for project: {project_url} (Hash: {url_hash})")

        # Fetch project ID from GitLab
        parsed_url = quote(project_url.strip('/'), safe='')
        project_data = gl.http_get(f"/projects/{parsed_url}")
        project_id = project_data["id"]

        # Fetch metrics
        project_obj = gl.projects.get(project_id)
        commits = project_obj.commits.list(since=(datetime.utcnow() - timedelta(days=N_DAYS)).isoformat() + "Z", all=True)
        commit_count = len(commits)
        contributor_count = len({commit.author_email for commit in commits})
        branch_count = len(project_obj.branches.list(all=True))
        last_commit_date = max(commit.created_at for commit in commits)

        # Upsert into project_metrics table
        record = session.query(ProjectMetric).filter_by(input_id=url_hash).first()
        if not record:
            record = ProjectMetric(
                id=project_id,
                input_id=url_hash,
                commit_count=commit_count,
                contributor_count=contributor_count,
                branch_count=branch_count,
                last_commit_date=last_commit_date,
            )
            session.add(record)
        else:
            record.commit_count = commit_count
            record.contributor_count = contributor_count
            record.branch_count = branch_count
            record.last_commit_date = last_commit_date
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing metrics: {e}")
        raise

@task
def process_language_row(project_id):
    """Process languages for a single project based on `project_id`."""
    try:
        logger.info(f"Processing languages for project ID: {project_id}")

        # Fetch languages from GitLab API
        project_obj = gl.projects.get(project_id)
        languages = project_obj.languages()

        # Clear old languages for the project
        session.query(ProjectLanguage).filter_by(project_id=project_id).delete()

        # Insert new languages
        for language, percentage in languages.items():
            session.add(ProjectLanguage(project_id=project_id, language=language, percentage=str(percentage)))
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing languages: {e}")
        raise

@dag(
    dag_id="metrics_parallel",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_tasks=10,  # Limit concurrent tasks
)
def metrics_parallel():
    # Load CSV rows in parallel
    df = pd.read_csv(INPUT_FILE)
    load_csv_task = load_csv_row.expand(row=df.to_dict(orient="records"))

    # Process metrics for each project in parallel
    input_projects = session.query(InputProject).all()
    metrics_task = process_metrics_row.expand(project=input_projects)

    # Process languages for each project in parallel
    project_ids = [metric.id for metric in session.query(ProjectMetric).all()]
    languages_task = process_language_row.expand(project_id=project_ids)

    # Define dependencies
    load_csv_task >> metrics_task >> languages_task

dag = metrics_parallel()
