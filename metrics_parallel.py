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
from urllib.parse import urlparse, quote

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

class ProjectMetric(Base):
    __tablename__ = "project_metrics"
    id = Column(Integer, primary_key=True)  # GitLab Project ID
    input_project_id = Column(String)  # Foreign key to InputProject.id
    commit_count = Column(Integer)
    contributor_count = Column(Integer)
    branch_count = Column(Integer)
    last_commit_date = Column(DateTime)

class ProjectLanguage(Base):
    __tablename__ = "project_languages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer)  # Foreign key to ProjectMetric.id
    language_name = Column(String)
    percentage = Column(Float)

# Initialize SQLAlchemy
engine = create_engine(DB_CONNECTION)
Session = sessionmaker(bind=engine)

# Hashing Function
def generate_hash(url):
    """Generate a SHA256 hash for the given URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def encode_gitlab_project_url(project_url):
    """Encode GitLab project URL for API requests."""
    parsed_url = urlparse(project_url)
    project_path = parsed_url.path.strip("/")
    encoded_path = quote(project_path, safe="")
    return encoded_path

@task
def load_csv_to_db():
    """Load CSV into input_projects table using hashed IDs."""
    session = Session()
    try:
        # Truncate the table
        session.execute("TRUNCATE TABLE input_projects RESTART IDENTITY CASCADE;")
        logger.info("Truncated input_projects table.")

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

def fetch_metrics(project_obj):
    """Fetch metrics (commits, contributors, branches, and last commit date) for a project."""
    try:
        # Fetch commits
        commits = project_obj.commits.list(since=(datetime.utcnow() - timedelta(days=N_DAYS)).isoformat() + "Z")
        commit_count = len(commits)

        # Fetch contributors
        contributor_count = len({commit.author_email for commit in commits})

        # Fetch branches
        branch_count = len(project_obj.branches.list())

        # Fetch last commit date
        last_commit_date = max(commit.created_at for commit in commits) if commits else None

        logger.info(
            f"Metrics fetched: commits={commit_count}, contributors={contributor_count}, "
            f"branches={branch_count}, last_commit_date={last_commit_date}"
        )

        return {
            "commit_count": commit_count,
            "contributor_count": contributor_count,
            "branch_count": branch_count,
            "last_commit_date": last_commit_date,
        }
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        return {
            "commit_count": 0,
            "contributor_count": 0,
            "branch_count": 0,
            "last_commit_date": None,
        }

def upsert_project_metric(session, project_id, metrics, input_project_id):
    """Upsert a ProjectMetric record."""
    metric = ProjectMetric(
        id=project_id,
        input_project_id=input_project_id,
        commit_count=metrics["commit_count"],
        contributor_count=metrics["contributor_count"],
        branch_count=metrics["branch_count"],
        last_commit_date=metrics["last_commit_date"],
    )
    try:
        session.merge(metric)  # Upsert using merge
        session.commit()
        logger.info(f"Upserted metrics for project ID: {project_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error upserting metrics for project ID {project_id}: {e}")

def persist_languages(session, project_id, languages):
    """Persist languages in the `project_languages` table."""
    try:
        # Clear existing languages
        session.query(ProjectLanguage).filter_by(project_id=project_id).delete()

        # Insert new languages
        for language, percentage in languages.items():
            session.add(
                ProjectLanguage(
                    project_id=project_id,
                    language_name=language,
                    percentage=percentage,
                )
            )
        session.commit()
        logger.info(f"Persisted languages for project ID: {project_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error persisting languages for project ID {project_id}: {e}")

@task
def process_metrics(batch_number):
    """Fetch and process metrics for a batch of projects."""
    session = Session()
    try:
        projects = fetch_batch(session, InputProject, batch_number, batch_size=BATCH_SIZE)
        if not projects:
            logger.info(f"No projects found in batch {batch_number}.")
            return

        for project in projects:
            try:
                # Properly encode the GitLab project path
                encoded_path = encode_gitlab_project_url(project.gitlab_project_url)
                gl_project = gl.http_get(f"/projects/{encoded_path}")
                project_obj = gl.projects.get(gl_project["id"])

                # Fetch metrics
                metrics = fetch_metrics(project_obj)

                # Upsert metrics
                upsert_project_metric(session, gl_project["id"], metrics, project.id)
            except gitlab.exceptions.GitlabGetError as e:
                logger.error(f"Project not found in GitLab for URL: {project.gitlab_project_url} - {e}")
                continue  # Skip this project and continue with the next one
            except Exception as e:
                logger.error(f"Error processing project: {project.gitlab_project_url} - {e}")
                continue  # Skip this project and continue with the next one
    finally:
        session.close()


@task
def fetch_languages(batch_number):
    """Fetch and persist languages for a batch of projects."""
    session = Session()
    try:
        # Fetch a batch of metrics
        metrics = fetch_batch(session, ProjectMetric, batch_number, batch_size=BATCH_SIZE)
        if not metrics:
            logger.info(f"No metrics found in batch {batch_number}.")
            return

        for metric in metrics:
            try:
                logger.info(f"Fetching languages for project ID: {metric.id}")

                # Fetch languages from GitLab API
                project_obj = gl.projects.get(metric.id)
                languages = project_obj.languages()

                # Log if no languages are found
                if not languages:
                    logger.warning(f"No languages found for project ID: {metric.id}")
                    continue

                # Clear old languages for the project
                deleted_count = session.query(ProjectLanguage).filter_by(project_id=metric.id).delete()
                logger.info(f"Deleted {deleted_count} old languages for project ID: {metric.id}")

                # Insert new languages
                for language, percentage in languages.items():
                    session.add(
                        ProjectLanguage(
                            project_id=metric.id,
                            language_name=language,
                            percentage=percentage,
                        )
                    )
                session.commit()
                logger.info(f"Persisted {len(languages)} languages for project ID: {metric.id}")

            except gitlab.exceptions.GitlabGetError as e:
                logger.error(f"Error fetching project for metric ID: {metric.id} - {e}")
                continue
            except Exception as e:
                session.rollback()
                logger.error(f"Error processing languages for project ID: {metric.id} - {e}")
                continue
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
    max_active_tasks=10,
) as dag:

    load_csv = load_csv_to_db()

    with TaskGroup("process_metrics_group") as process_metrics_group:
        for batch_num in range(10):  # Dynamically calculate the number of batches
            process_metrics(batch_number=batch_num)

    with TaskGroup("process_languages_group") as process_languages_group:
        for batch_num in range(10):  # Dynamically calculate the number of batches
            fetch_languages(batch_number=batch_num)

    load_csv >> process_metrics_group >> process_languages_group
