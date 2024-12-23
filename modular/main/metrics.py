from git import Repo
from datetime import datetime
import pytz
from sqlalchemy.dialects.postgresql import insert
from models import Session, RepoMetrics

def calculate_and_persist_repo_metrics(repo_dir, repo, session):
    """Calculate and persist repository metrics."""
    logger.info(f"Starting metrics calculation for repository: {repo.repo_name} (ID: {repo.repo_id})")

    # Check if the repository directory exists
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)
    else:
        logger.debug(f"Repository directory found: {repo_dir}")

    # Access the repository using GitPython
    repo_obj = Repo(repo_dir)
    default_branch = repo_obj.active_branch.name
    logger.debug(f"Default branch detected: {default_branch}")

    # Calculate metrics
    total_size = sum(blob.size for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    file_count = sum(1 for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    total_commits = sum(1 for _ in repo_obj.iter_commits(default_branch))
    contributors = set(commit.author.email for commit in repo_obj.iter_commits(default_branch))
    last_commit_date = max(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    first_commit_date = min(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    repo_age_days = (datetime.utcnow().replace(tzinfo=pytz.utc) - first_commit_date).days

    # Log calculated metrics
    logger.info(f"Metrics for {repo.repo_name} (ID: {repo.repo_id}):")
    logger.info(f"  Total Size: {total_size} bytes")
    logger.info(f"  File Count: {file_count}")
    logger.info(f"  Total Commits: {total_commits}")
    logger.info(f"  Number of Contributors: {len(contributors)}")
    logger.info(f"  Last Commit Date: {last_commit_date}")
    logger.info(f"  Repository Age: {repo_age_days} days")
    logger.info(f"  Active Branch Count: {len(repo_obj.branches)}")

    # Persist metrics in the database
    session.execute(
        insert(RepoMetrics).values(
            repo_id=repo.repo_id,
            repo_size_bytes=total_size,
            file_count=file_count,
            total_commits=total_commits,
            number_of_contributors=len(contributors),
            last_commit_date=last_commit_date,
            repo_age_days=repo_age_days,
            active_branch_count=len(repo_obj.branches)
        ).on_conflict_do_update(
            index_elements=['repo_id'],
            set_={"repo_size_bytes": total_size, "file_count": file_count, "updated_at": datetime.utcnow()}
        )
    )
    session.commit()
    logger.info(f"Metrics saved for repository: {repo.repo_name} (ID: {repo.repo_id})")

if __name__ == "__main__":
    import os
    import logging

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Hardcoded values for standalone execution
    repo_slug = "example-repo"
    repo_id = "example-repo-id"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)

    # Define the path to the cloned repository
    repo_dir = f"/mnt/tmpfs/cloned_repositories/{repo.repo_slug}"

    # Create a session and run metrics calculation
    session = Session()
    try:
        logger.info(f"Running metrics calculation for hardcoded repo_id: {repo.repo_id}, repo_slug: {repo.repo_slug}")
        calculate_and_persist_repo_metrics(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during standalone metrics calculation: {e}")
    finally:
        session.close()
        logger.info("Session closed.")
