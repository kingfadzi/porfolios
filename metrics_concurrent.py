from airflow import DAG
from airflow.decorators import task, dag
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
import gitlab
import pandas as pd
from urllib.parse import urlparse, quote
import logging

# Configuration
GITLAB_URL = "https://gitlab.example.com"
PRIVATE_TOKEN = "your_private_token"
DB_NAME = "your_db_name"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_HOST = "localhost"
DB_PORT = 5432
INPUT_FILE = "/path/to/input_projects.csv"
N_DAYS = 7  # Number of days to look back for commits

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# SQLAlchemy Base and ORM Model
Base = declarative_base()

class ProjectMetric(Base):
    __tablename__ = "project_metrics"
    project_id = Column(Integer, primary_key=True)
    gitlab_project_url = Column(String, unique=True)
    commit_count = Column(Integer)
    contributor_count = Column(Integer)
    branch_count = Column(Integer)
    lob = Column(String)
    dpt = Column(String)
    project_name = Column(String)
    appid = Column(String)
    appname = Column(String)
    gitlab_workspace = Column(String)

# Initialize GitLab client
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

# Create database engine and session
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

def get_project_id_from_url(project_url):
    try:
        logger.info(f"Fetching project ID for URL: {project_url}")
        parsed_url = urlparse(project_url)
        project_path = parsed_url.path.strip("/")
        encoded_path = quote(project_path, safe="")
        project = gl.http_get(f"/projects/{encoded_path}")
        project_id = project["id"]
        logger.info(f"Fetched project ID: {project_id} for URL: {project_url}")
        return project_id
    except Exception as e:
        logger.error(f"Error fetching project ID for URL: {project_url} - {e}")
        raise

def fetch_commits_last_n_days(project_id, days):
    try:
        logger.info(f"Fetching commits for project ID: {project_id} for the last {days} days")
        since_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        until_date = datetime.utcnow().isoformat() + "Z"
        logger.debug(f"Commit API parameters - since: {since_date}, until: {until_date}")

        project = gl.projects.get(project_id)
        commits = project.commits.list(since=since_date, until=until_date, all=True)
        logger.info(f"Fetched {len(commits)} commits for project ID: {project_id}")
        return len(commits)
    except Exception as e:
        logger.error(f"Error fetching commits for project ID {project_id}: {e}")
        raise

def fetch_contributor_count(project_id):
    try:
        logger.info(f"Fetching contributors for project ID: {project_id}")
        endpoint = f"/projects/{project_id}/repository/contributors"
        response = gl.http_get(endpoint)
        contributors = response if isinstance(response, list) else []
        logger.info(f"Fetched {len(contributors)} contributors for project ID: {project_id}")
        return len(contributors)
    except Exception as e:
        logger.error(f"Error fetching contributors for project ID {project_id}: {e}")
        raise

def fetch_branch_count(project_id):
    """
    Fetch the number of branches for a GitLab project.
    """
    try:
        logger.info(f"Fetching branches for project ID: {project_id}")
        project = gl.projects.get(project_id)
        branches = project.branches.list(all=True)
        logger.info(f"Fetched {len(branches)} branches for project ID: {project_id}")
        return len(branches)
    except Exception as e:
        logger.error(f"Error fetching branches for project ID {project_id}: {e}")
        raise

def upsert_with_orm(project_id, project_url, metrics, extra_data):
    try:
        logger.info(f"Upserting metrics for project ID: {project_id}")
        record = session.query(ProjectMetric).filter_by(project_id=project_id).first()
        if record:
            record.commit_count = metrics["commit_count"]
            record.contributor_count = metrics["contributor_count"]
            record.branch_count = metrics["branch_count"]
            record.lob = extra_data["lob"]
            record.dpt = extra_data["dpt"]
            record.project_name = extra_data["project_name"]
            record.appid = extra_data["appid"]
            record.appname = extra_data["appname"]
            record.gitlab_workspace = extra_data["gitlab_workspace"]
        else:
            record = ProjectMetric(
                project_id=project_id,
                gitlab_project_url=project_url,
                **metrics,
                **extra_data
            )
            session.add(record)
        session.commit()
        logger.info(f"Upserted metrics for project ID: {project_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error during upsert for project ID {project_id}: {e}")
        raise

@task
def process_project(row):
    try:
        project_url = row["gitlab_project_url"].strip()
        logger.info(f"Starting processing for project URL: {project_url}")

        # Fetch project ID
        project_id = get_project_id_from_url(project_url)

        # Fetch metrics
        commit_count = fetch_commits_last_n_days(project_id, N_DAYS)
        contributor_count = fetch_contributor_count(project_id)
        branch_count = fetch_branch_count(project_id)

        # Compile metrics
        metrics = {
            "commit_count": commit_count,
            "contributor_count": contributor_count,
            "branch_count": branch_count,
        }

        # Extract extra data
        extra_data = {
            "lob": row["LOB"],
            "dpt": row["dpt"],
            "project_name": row["project_name"],
            "appid": row["appid"],
            "appname": row["appname"],
            "gitlab_workspace": row["gitlab_workspace"]
        }

        # Upsert data into the database
        upsert_with_orm(project_id, project_url, metrics, extra_data)

        logger.info(f"Completed processing for project URL: {project_url}")

    except Exception as e:
        logger.error(f"Error processing project URL: {project_url} - {e}")
        raise

@dag(
    dag_id="gitlab_pipeline_with_branches",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
)
def gitlab_pipeline_with_branches():
    logger.info("Starting DAG: GitLab Pipeline with Branch Count")
    df = pd.read_csv(INPUT_FILE)
    rows = df.to_dict(orient="records")
    process_project.expand(row=rows)

dag = gitlab_pipeline_with_branches()
