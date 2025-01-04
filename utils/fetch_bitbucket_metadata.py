import logging
from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from sqlalchemy import create_engine, Column, String, Boolean, BigInteger, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from atlassian import Bitbucket
from itertools import islice
import os

# Airflow logger
log = logging.getLogger("airflow.task")

# Configuration
BITBUCKET_URL = os.getenv("BITBUCKET_URL", "https://xx.yy.com")
TOKEN = os.getenv("BITBUCKET_TOKEN", "your_personal_access_token")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost:5432/bitbucket_db")

# Initialize database connection
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# ORM Models
class Project(Base):
    __tablename__ = "bitbucket_projects"

    project_key = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    description = Column(String)
    is_private = Column(Boolean)
    created_on = Column(DateTime)
    updated_on = Column(DateTime)

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

# Create tables if not exist
Base.metadata.create_all(engine)

# Initialize Bitbucket API
bitbucket = Bitbucket(
    url=BITBUCKET_URL,
    token=TOKEN,
    cloud=False,
    verify_ssl=False
)

# Helper function for chunking
def chunk_list(data, chunk_size):
    """Yield successive chunk_size chunks from data."""
    it = iter(data)
    for first in it:
        yield [first] + list(islice(it, chunk_size - 1))

# Define the DAG
default_args = {
    "start_date": days_ago(1),
    "retries": 3,
}

with DAG(
    dag_id="fetch_bitbucket_metadata",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    @task()
    def fetch_projects():
        """Fetch all projects from Bitbucket and store them in the database."""
        log.info("Starting to fetch projects from Bitbucket...")
        session = Session()
        try:
            # Fetch and convert generator to list
            projects = list(bitbucket.project_list())
            log.info(f"Fetched {len(projects)} projects from Bitbucket.")

            for project in projects:
                project_data = Project(
                    project_key=project["key"],
                    project_name=project["name"],
                    description=project.get("description"),
                    is_private=project.get("public", False)
                )
                session.merge(project_data)  # Upsert the project
                log.debug(f"Upserted project: {project['key']} - {project['name']}")
            session.commit()
        except Exception as e:
            log.error("Failed to fetch or store projects.", exc_info=True)
            raise
        finally:
            session.close()

        return [project["key"] for project in projects]

    @task()
    def chunk_project_keys(project_keys):
        """Split project keys into manageable chunks."""
        chunk_size = 100  # Adjust chunk size as needed
        chunks = list(chunk_list(project_keys, chunk_size))
        log.info(f"Split {len(project_keys)} projects into {len(chunks)} chunks of size {chunk_size}.")
        return chunks

    @task()
    def process_project_chunk(project_chunk):
        """Process a single chunk of project keys."""
        session = Session()
        try:
            for project_key in project_chunk:
                log.info(f"Fetching repositories for project {project_key}...")
                repos = list(bitbucket.repo_list(project_key))
                log.info(f"Fetched {len(repos)} repositories for project {project_key}.")

                for repo in repos:
                    repo_data = Repository(
                        repo_id=f"{project_key}/{repo['slug']}",
                        project_key=project_key,
                        repo_name=repo["name"],
                        repo_slug=repo["slug"],
                        clone_url_https=repo["links"]["clone"][0]["href"] if repo["links"]["clone"][0]["name"] == "https" else None,
                        clone_url_ssh=repo["links"]["clone"][1]["href"] if len(repo["links"]["clone"]) > 1 else None,
                        language=repo.get("language"),
                        size=repo.get("size"),
                        forks=repo.get("forks_count", 0),
                        created_on=repo.get("created_on"),
                        updated_on=repo.get("updated_on")
                    )
                    session.merge(repo_data)  # Upsert the repository
                    log.debug(f"Upserted repository: {repo['slug']} - {repo['name']}")
                session.commit()
                log.info(f"Repositories for project {project_key} stored successfully.")
        except Exception as e:
            log.error(f"Failed to fetch or store repositories for chunk {project_chunk}.", exc_info=True)
            raise
        finally:
            session.close()

    # Task 1: Fetch all projects
    project_keys = fetch_projects()

    # Task 2: Chunk project keys into manageable sizes
    project_chunks = chunk_project_keys(project_keys=project_keys)

    # Task 3: Process each chunk in parallel
    process_project_chunk.expand(project_chunk=project_chunks)
