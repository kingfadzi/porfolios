from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task, dag
from datetime import datetime
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
    lob = Column(String)  # Line of Business
    dpt = Column(String)  # Department
    project_name = Column(String)  # Project Name
    appid = Column(String)  # Application ID
    appname = Column(String)  # Application Name
    gitlab_workspace = Column(String)  # GitLab Workspace

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

def fetch_metrics(project_id):
    try:
        logger.info(f"Fetching metrics for project ID: {project_id}")
        commit_count = len(gl.projects.get(project_id).commits.list(all=True))
        contributor_count = len(gl.projects.get(project_id).repository_contributors())
        branch_count = len(gl.projects.get(project_id).branches.list(all=True))
        metrics = {
            "commit_count": commit_count,
            "contributor_count": contributor_count,
            "branch_count": branch_count,
        }
        logger.info(f"Fetched metrics for project ID: {project_id} - {metrics}")
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics for project ID: {project_id} - {e}")
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
        project_id = get_project_id_from_url(project_url)
        metrics = fetch_metrics(project_id)
        extra_data = {
            "lob": row["LOB"],
            "dpt": row["dpt"],
            "project_name": row["project_name"],
            "appid": row["appid"],
            "appname": row["appname"],
            "gitlab_workspace": row["gitlab_workspace"]
        }
        upsert_with_orm(project_id, project_url, metrics, extra_data)
        logger.info(f"Completed processing for project URL: {project_url}")
    except Exception as e:
        logger.error(f"Error processing project URL: {project_url} - {e}")

@dag(
    dag_id="gitlab_pipeline_with_extra_fields",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
)
def gitlab_pipeline_with_extra_fields():
    logger.info("Starting DAG: GitLab Pipeline with Extra Fields")
    df = pd.read_csv(INPUT_FILE)
    for _, row in df.iterrows():
        process_project(row.to_dict())

dag = gitlab_pipeline_with_extra_fields()
