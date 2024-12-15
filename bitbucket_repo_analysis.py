from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, ForeignKey, BigInteger, DateTime
from datetime import datetime
import os
import subprocess

# Database configuration
DB_URL = "postgresql+psycopg2://username:password@localhost/repo_analysis"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Repository ORM model
class Repository(Base):
    __tablename__ = "bitbucket_repositories"
    repo_id = Column(String, primary_key=True)  # Unique identifier (e.g., slug)
    project_key = Column(String, ForeignKey("bitbucket_projects.project_key"))
    repo_name = Column(String, nullable=False)
    repo_slug = Column(String, nullable=False)
    clone_url_https = Column(String)
    clone_url_ssh = Column(String)
    language = Column(String)
    size = Column(BigInteger)
    forks = Column(BigInteger)
    created_on = Column(DateTime)
    updated_on = Column(DateTime)

# Analysis results ORM model
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    repo_id = Column(String, ForeignKey("bitbucket_repositories.repo_id"))
    language = Column(String, nullable=False)
    percent_usage = Column(BigInteger, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)

# Function to process a single repository
def analyze_repo(repo_id, **kwargs):
    session = Session()
    repo = session.query(Repository).filter(Repository.repo_id == repo_id).first()

    if not repo:
        raise ValueError(f"Repository with repo_id {repo_id} not found!")

    try:
        # Determine the clone URL (SSH preferred)
        clone_url = repo.clone_url_ssh or repo.clone_url_https
        if not clone_url:
            raise ValueError(f"No clone URL found for repository {repo.repo_name} (ID: {repo.repo_id})")

        # Clone the repository
        repo_dir = f"/tmp/{repo.repo_slug}"
        os.system(f"git clone {clone_url} {repo_dir}")

        # Run go-enry analysis
        analysis_file = f"{repo_dir}_analysis.txt"
        subprocess.run(f"go-enry {repo_dir} > {analysis_file}", shell=True, check=True)

        # Parse go-enry output
        with open(analysis_file, 'r') as f:
            lines = f.readlines()
        results = [line.strip().split(',') for line in lines]

        # Save results to database
        for language, percent_usage in results:
            session.add(AnalysisResult(
                repo_id=repo.repo_id,
                language=language,
                percent_usage=int(percent_usage)
            ))

        # Commit results
        session.commit()

    except Exception as e:
        session.rollback()
        raise e

    finally:
        # Clean up temporary files
        os.system(f"rm -rf {repo_dir}")
        session.close()

# Airflow DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 15),
    'retries': 1,
}

with DAG('bitbucket_repo_analysis', default_args=default_args, schedule_interval=None, concurrency=20) as dag:
    session = Session()
    repositories = session.query(Repository).all()
    session.close()

    for repo in repositories:
        PythonOperator(
            task_id=f"analyze_repo_{repo.repo_id}",
            python_callable=analyze_repo,
            op_kwargs={'repo_id': repo.repo_id},
            dag=dag
        )
