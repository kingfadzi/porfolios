from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
import gitlab
import pandas as pd
from urllib.parse import urlparse, quote

# Configuration
GITLAB_URL = "https://gitlab.example.com"
PRIVATE_TOKEN = "your_private_token"
DB_NAME = "your_db_name"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_HOST = "localhost"
DB_PORT = 5432
INPUT_FILE = "/path/to/input_projects.csv"

# SQLAlchemy Base and ORM Model
Base = declarative_base()

class ProjectMetric(Base):
    __tablename__ = "project_metrics"
    project_id = Column(Integer, primary_key=True)
    gitlab_project_url = Column(String, unique=True)
    commit_count = Column(Integer)
    contributor_count = Column(Integer)
    branch_count = Column(Integer)

# Initialize GitLab client
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

# Create database engine and session
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

def get_project_id_from_url(project_url):
    parsed_url = urlparse(project_url)
    project_path = parsed_url.path.strip("/")
    encoded_path = quote(project_path, safe="")
    project = gl.http_get(f"/projects/{encoded_path}")
    return project["id"]

def fetch_metrics(project_id):
    commit_count = len(gl.projects.get(project_id).commits.list(all=True))
    contributor_count = len(gl.projects.get(project_id).repository_contributors())
    branch_count = len(gl.projects.get(project_id).branches.list(all=True))
    return {
        "commit_count": commit_count,
        "contributor_count": contributor_count,
        "branch_count": branch_count,
    }

def upsert_with_orm(project_id, project_url, metrics):
    try:
        record = session.query(ProjectMetric).filter_by(project_id=project_id).first()
        if record:
            # Update existing record
            record.commit_count = metrics["commit_count"]
            record.contributor_count = metrics["contributor_count"]
            record.branch_count = metrics["branch_count"]
        else:
            # Insert new record
            record = ProjectMetric(
                project_id=project_id,
                gitlab_project_url=project_url,
                **metrics
            )
            session.add(record)
        session.commit()
        print(f"Upserted project_id: {project_id}")
    except Exception as e:
        session.rollback()
        print(f"Error during upsert for project_id {project_id}: {e}")

def process_project(project_url):
    try:
        project_id = get_project_id_from_url(project_url)
        metrics = fetch_metrics(project_id)
        upsert_with_orm(project_id, project_url, metrics)
    except Exception as e:
        print(f"Error processing {project_url}: {e}")

def process_projects():
    # Create the table if it doesn't exist
    Base.metadata.create_all(engine)

    # Read input CSV
    df = pd.read_csv(INPUT_FILE)
    for _, row in df.iterrows():
        project_url = row["gitlab_project_url"].strip()
        if not project_url:
            continue
        process_project(project_url)

# Define Airflow DAG
with DAG(
    dag_id="gitlab_pipeline_orm",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,  # Trigger manually
    catchup=False
) as dag:
    process_projects_task = PythonOperator(
        task_id="process_projects",
        python_callable=process_projects
    )
