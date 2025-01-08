import logging
from datetime import datetime, timezone
from urllib.parse import urlparse
import re
import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from modular.models import Repository  # Importing the Repository model

# PostgreSQL credentials
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "192.168.1.188"
DB_PORT = "5422"
DB_NAME = "gitlab-usage"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def parse_gitlab_url(url):
    """
    Parses Git URLs (HTTPS or SSH) and extracts necessary components.

    :param url: The Git URL (either HTTPS or SSH).
    :return: A dictionary with parsed components.
    """
    if url.startswith("https://"):
        # Parse HTTPS URLs
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) < 2:
            raise ValueError(f"Invalid URL format: {url}")

        org = path_parts[0]  # Extract the organization
        repo_path = "/".join(path_parts[1:])  # Extract the remaining path as repo_id
        project = path_parts[-1].replace(".git", "")  # Extract the project name, removing '.git'

        return {
            "repo_id": repo_path,
            "repo_name": project,
            "repo_slug": project,
            "host_name": parsed.netloc,
            "org": org
        }

    elif url.startswith("git@"):
        # Parse SSH URLs (e.g., git@host:org/repo.git)
        match = re.match(r"git@([\w\.\-]+):([\w\-/]+)\.git", url)
        if not match:
            raise ValueError(f"Invalid SSH URL format: {url}")

        host_name = match.group(1)
        repo_path = match.group(2)
        path_parts = repo_path.split("/")

        if len(path_parts) < 2:
            raise ValueError(f"Invalid SSH URL format: {url}")

        org = path_parts[0]
        project = path_parts[-1]

        return {
            "repo_id": repo_path,
            "repo_name": project,
            "repo_slug": project,
            "host_name": host_name,
            "org": org
        }

    else:
        raise ValueError(f"Unsupported URL format: {url}")


def read_urls(input_file):
    """
    Reads the input file containing one URL per line.

    :param input_file: Path to the input file.
    :return: Pandas DataFrame with a single 'url' column.
    """
    # Read the file as a single-column DataFrame
    df = pd.read_csv(input_file, header=None, names=["url"], dtype=str)

    # Drop rows where 'url' is NaN or empty
    df = df.dropna(subset=["url"])
    df = df[df["url"].str.strip() != ""]

    # Add a placeholder 'app_id' column (optional)
    df["app_id"] = None

    return df

def create_repository_objects(dataframe):
    """
    Converts DataFrame rows into repository dictionaries.

    :param dataframe: Pandas DataFrame with app_id (optional) and url columns.
    :return: List of repository dictionaries.
    """
    repositories = []
    for _, row in dataframe.iterrows():
        parsed = parse_gitlab_url(row["url"])

        # Generate the SSH clone URL
        ssh_url = f"git@{parsed['host_name']}:{parsed['org']}/{parsed['repo_id']}.git"

        repositories.append({
            "repo_id": parsed["repo_id"],
            "app_id": row["app_id"],  # Will be None if app_id is missing
            "repo_name": parsed["repo_name"],
            "repo_slug": parsed["repo_slug"],
            "host_name": parsed["host_name"],
            "status": "NEW",
            "clone_url_ssh": ssh_url,
            "comment": None,
            "updated_on": datetime.now(timezone.utc)
        })
    logger.info(f"Prepared {len(repositories)} repository records for upsert")
    return repositories


def upsert_repositories(repositories, engine):
    """
    Performs an upsert (insert or update) of repository records into the database.

    :param repositories: List of repository dictionaries.
    :param engine: SQLAlchemy engine connected to the database.
    """
    if not repositories:
        logger.warning("No repositories to upsert.")
        return

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        stmt = pg_insert(Repository).values(repositories)
        stmt = stmt.on_conflict_do_update(
            index_elements=['repo_id'],
            set_={
                "app_id": stmt.excluded.app_id,
                "repo_name": stmt.excluded.repo_name,
                "repo_slug": stmt.excluded.repo_slug,
                "clone_url_ssh": stmt.excluded.clone_url_ssh,
                "host_name": stmt.excluded.host_name,
                "status": stmt.excluded.status,
                "comment": stmt.excluded.comment,
                "updated_on": stmt.excluded.updated_on
            }
        )
        session.execute(stmt)
        session.commit()
        logger.info(f"Upserted {len(repositories)} repositories into the database.")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error during upsert: {e}")
    finally:
        session.close()


def main():
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Load repository data into the database.")
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input CSV file containing app_id (optional) and repository URLs."
    )
    args = parser.parse_args()
    input_file = args.input_file

    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    try:
        engine = create_engine(db_url)
        logger.info("Connected to the PostgreSQL database.")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database engine: {e}")
        return

    df = read_urls(input_file)
    repositories = create_repository_objects(df)
    upsert_repositories(repositories, engine)


if __name__ == "__main__":
    main()