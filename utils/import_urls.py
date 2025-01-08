import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Example SQLAlchemy model (update with your actual import)
from modular.models import Repository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

class RepositoryLoader:
    # Hardcoded DB URL; adjust as needed
    DB_URL = "postgresql://postgres:postgres@192.168.1.188:5422/gitlab-usage"

    def __init__(self):
        """
        Creates the database engine and sessionmaker using the hardcoded DB URL.
        """
        try:
            self.engine = create_engine(self.DB_URL)
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"Connected to database: {self.DB_URL}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database engine: {e}")
            raise

    def deduplicate_file(self, input_file, output_file):
        """
        Removes duplicate lines from a file and saves the result.
        """
        with open(input_file, "r") as infile:
            unique_lines = set(infile.readlines())

        with open(output_file, "w") as outfile:
            outfile.writelines(sorted(unique_lines))

        logger.info(f"Deduplicated file saved to {output_file}")

    def read_urls(self, file_path):
        """
        Reads the (deduplicated) file into a DataFrame with a single 'url' column.
        """
        df = pd.read_csv(file_path, header=None, names=["url"], dtype=str)
        df = df.dropna(subset=["url"])
        df = df[df["url"].str.strip() != ""]
        return df

    def ensure_ssh_url(self, url):
        """
        Ensures the given URL is in SSH format.

        - If it's already SSH (git@ or ssh://), return it as is.
        - If it's HTTPS for GitHub, Bitbucket, or GitLab, convert it to SSH.
        - Otherwise, raise ValueError.
        """
        # Already SSH?
        if url.startswith("ssh://") or url.startswith("git@"):
            return url

        # Must be HTTPS if not SSH
        if not url.startswith("https://"):
            raise ValueError(f"Unsupported URL format (not SSH or HTTPS): {url}")

        parsed = urlparse(url)
        host_name = parsed.netloc.lower()

        # GITHUB
        if host_name == "github.com":
            match = re.match(r"https://github\.com/([^/]+)/(.+?)(\.git)?$", url)
            if not match:
                raise ValueError(f"URL not recognized as valid GitHub URL: {url}")
            owner_or_org, repo_slug, _ = match.groups()
            return f"git@github.com:{owner_or_org}/{repo_slug}.git"

        # BITBUCKET (sample pattern; adjust if your Bitbucket URLs differ)
        elif "bitbucket" in host_name:
            # Example: https://bitbucket.org/<workspace>/<repo>.git
            match = re.match(r"https://([^/]+)/([^/]+)/(.+?)(\.git)?$", url)
            if not match:
                raise ValueError(f"URL not recognized as valid Bitbucket URL: {url}")
            domain, workspace, repo_slug, _ = match.groups()
            # For some setups, you might need a different port or path
            return f"git@{domain}:{workspace}/{repo_slug}.git"

        # GITLAB
        elif host_name == "gitlab.com":
            # Supports nested groups: group/subgroup/subsubgroup
            match = re.match(r"https://gitlab\.com/([^/]+(?:/[^/]+)*)/(.+?)(\.git)?$", url)
            if not match:
                raise ValueError(f"URL not recognized as valid GitLab URL: {url}")
            group_path, repo_slug, _ = match.groups()
            return f"git@gitlab.com:{group_path}/{repo_slug}.git"

        else:
            raise ValueError(f"Unsupported host '{host_name}' for URL: {url}")

    def parse_ssh_url(self, ssh_url):
        """
        Parses an SSH URL of the form:
            git@<host_name>:<nested_path>/<repo>[.git]
        and extracts the host_name and repo_path (repo_id).
        Raises ValueError if the URL is not valid SSH.
        """
        if not ssh_url.startswith("git@"):
            raise ValueError(f"Expected an SSH URL (git@...), got: {ssh_url}")

        match = re.match(r"git@([\w.\-]+):([\w\-/\.]+)(?:\.git)?", ssh_url)
        if not match:
            raise ValueError(f"Invalid SSH URL format: {ssh_url}")

        host_name = match.group(1)
        repo_path = match.group(2)  # e.g. org/suborg/subsuborg/repo
        return {
            "host_name": host_name,
            "repo_id": repo_path
        }

    def build_repository_object(self, raw_url):
        # Convert to SSH if needed
        ssh_url = self.ensure_ssh_url(raw_url)
        # Example result of ssh_url: "git@github.com:foo/bar/baz.git"

        components = self.parse_ssh_url(ssh_url)
        # components["repo_id"] might be "foo/bar/baz.git"

        # Split on "/"
        path_parts = components["repo_id"].split("/")
        # e.g. ["foo", "bar", "baz.git"]

        if len(path_parts) < 2:
            raise ValueError(f"Expected at least two path segments for {components['repo_id']}")

        # Take the last 2 segments
        second_last = path_parts[-2]
        last = path_parts[-1].replace(".git", "")  # remove .git if present

        # Construct the new repo_id (xxx/yyy)
        repo_id = f"{second_last}/{last}"
        # e.g. "bar/baz"

        # For the slug, you might just use the last segment
        repo_slug = last

        # For the name, you could do the same or something else
        # Here, let's say it's also last
        repo_name = last

        repository_data = {
            "repo_id": repo_id,                   # "bar/baz"
            "repo_name": repo_name,               # "baz"
            "repo_slug": repo_slug,               # "baz"
            "clone_url_ssh": ssh_url,             # "git@github.com:foo/bar/baz.git"
            "host_name": components["host_name"], # "github.com"
            "status": "NEW",
            "updated_on": datetime.now(timezone.utc),
        }
        return repository_data

    def upsert_repositories(self, repositories):
        """
        Perform an upsert (insert or update) of repository records into the database.
        """
        if not repositories:
            logger.warning("No repositories to upsert.")
            return

        session = self.Session()
        try:
            stmt = pg_insert(Repository).values(repositories)
            stmt = stmt.on_conflict_do_update(
                index_elements=["repo_id"],
                set_={
                    "host_name": stmt.excluded.host_name,
                    "clone_url_ssh": stmt.excluded.clone_url_ssh,
                    "status": stmt.excluded.status,
                    "updated_on": stmt.excluded.updated_on,
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

    def run(self, input_file):
        """
        Main entry point:
          1. Deduplicate the input file
          2. Read and parse each URL (convert HTTPS -> SSH if needed)
          3. Build a list of unique repo objects
          4. Upsert them into the DB
        """
        # 1. Deduplicate
        deduplicated_file = f"{input_file}.deduplicated"
        self.deduplicate_file(input_file, deduplicated_file)

        # 2. Read URLs
        df = self.read_urls(deduplicated_file)

        # 3. Validate / convert / parse -> build repository objects
        repositories = []
        seen_repo_ids = set()
        for url in df["url"]:
            try:
                repo_obj = self.build_repository_object(url)
                if repo_obj["repo_id"] in seen_repo_ids:
                    logger.warning(f"Duplicate repo_id skipped: {repo_obj['repo_id']}")
                    continue
                repositories.append(repo_obj)
                seen_repo_ids.add(repo_obj["repo_id"])
            except ValueError as e:
                logger.warning(f"Skipping invalid or unsupported URL {url}: {e}")
                continue

        # 4. Upsert
        self.upsert_repositories(repositories)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Load repository data into the database.")
    parser.add_argument("input_file", type=str, help="Path to the input file containing repository URLs.")
    args = parser.parse_args()

    loader = RepositoryLoader()
    loader.run(args.input_file)

if __name__ == "__main__":
    main()
