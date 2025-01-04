from atlassian import Bitbucket
from sqlalchemy import create_engine, Column, String, Boolean, BigInteger, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configuration
BITBUCKET_URL = os.getenv("BITBUCKET_URL", "https://xx.yy.com")
TOKEN = os.getenv("BITBUCKET_TOKEN", "your_personal_access_token")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost:5432/bitbucket_db")

# Initialize Bitbucket API
bitbucket = Bitbucket(
    url=BITBUCKET_URL,
    token=TOKEN,
    cloud=False,
    verify_ssl=False  # Ignore SSL errors if needed
)

# Initialize database connection
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Define ORM models
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

# Fetch and store project metadata
def fetch_and_store_projects(limit=10):
    projects = bitbucket.project_list()
    count = 0
    for project in projects:
        if count >= limit:  # Stop after 'limit' projects
            break
        # Extract project metadata
        project_data = Project(
            project_key=project["key"],
            project_name=project["name"],
            description=project.get("description"),
            is_private=project.get("public", False),
            created_on=None,  # Add API call to fetch timestamps if needed
            updated_on=None
        )
        # Upsert project metadata
        session.merge(project_data)
        count += 1
    session.commit()
    print(f"Stored metadata for {count} projects.")

# Fetch and store repository metadata
def fetch_and_store_repositories(limit=10):
    projects = session.query(Project).limit(limit).all()  # Limit to first 'limit' projects
    for project in projects:
        repos = bitbucket.repo_list(project.project_key)
        repo_count = 0
        for repo in repos:
            if repo_count >= limit:  # Stop after 'limit' repositories per project
                break
            # Extract repository metadata
            repo_data = Repository(
                repo_id=f"{project.project_key}/{repo['slug']}",
                project_key=project.project_key,
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
            # Upsert repository metadata
            session.merge(repo_data)
            repo_count += 1
        print(f"Stored metadata for {repo_count} repositories in project {project.project_key}.")
    session.commit()

if __name__ == "__main__":
    print("Fetching and storing project metadata...")
    fetch_and_store_projects(limit=10)

    print("Fetching and storing repository metadata...")
    fetch_and_store_repositories(limit=10)
