from git import Repo, GitCommandError, InvalidGitRepositoryError
from datetime import datetime, timezone
import pytz
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, RepoMetrics
from modular.execution_decorator import analyze_execution

import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@analyze_execution(session_factory=Session, stage="Git Log Analysis")
def run_gitlog_analysis(repo_dir, repo, session, run_id=None):
    """
    Calculate and persist repository metrics.

    :param repo_dir: Directory path of the repository to be analyzed.
    :param repo: Repository object containing metadata like repo_id and repo_slug.
    :param session: Database session to persist the results.
    :param run_id: DAG run ID passed for tracking.
    :return: Success message with all processed metrics or raises an exception on failure.
    """
    logger.info(f"Starting metrics calculation for repository: {repo.repo_name} (ID: {repo.repo_id})")

    # Check if the repository directory exists
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # Access the repository using GitPython
    repo_obj = get_repo_object(repo_dir)
    if not repo_obj:
        error_message = f"Failed to access Git repository at {repo_dir}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    if repo_obj.head.is_detached:
        logger.warning("Repository is in detached HEAD state")
        default_branch = None
    else:
        default_branch = repo_obj.active_branch.name
        logger.info(f"The default branch is: {default_branch}")

    if not default_branch:
        raise RuntimeError("Unable to determine the default branch of the repository.")

    logger.info(f"Calculating metrics from gitlog for repository directory: {repo_dir}")

    # Calculate metrics
    total_size = sum(blob.size for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    file_count = sum(1 for blob in repo_obj.tree(default_branch).traverse() if blob.type == 'blob')
    total_commits = sum(1 for _ in repo_obj.iter_commits(default_branch))
    contributors = set(commit.author.email for commit in repo_obj.iter_commits(default_branch))
    last_commit_date = max(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    first_commit_date = min(commit.committed_datetime for commit in repo_obj.iter_commits(default_branch))
    repo_age_days = (datetime.now(timezone.utc) - first_commit_date).days
    active_branch_count = len(repo_obj.branches)

    # Log calculated metrics
    logger.info(f"Metrics for {repo.repo_name} (ID: {repo.repo_id}):")
    logger.info(f"  Total Size: {total_size} bytes")
    logger.info(f"  File Count: {file_count}")
    logger.info(f"  Total Commits: {total_commits}")
    logger.info(f"  Number of Contributors: {len(contributors)}")
    logger.info(f"  Last Commit Date: {last_commit_date}")
    logger.info(f"  Repository Age: {repo_age_days} days")
    logger.info(f"  Active Branch Count: {active_branch_count}")

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
            active_branch_count=active_branch_count
        ).on_conflict_do_update(
            index_elements=['repo_id'],
            set_={
                "repo_size_bytes": total_size,
                "file_count": file_count,
                "updated_at": datetime.now(timezone.utc)  # Updated to use timezone-aware datetime
            }
        )
    )
    session.commit()
    logger.info(f"Metrics saved for repository: {repo.repo_name} (ID: {repo.repo_id})")

    # Return all metrics in a single statement
    return (
        f"{repo.repo_name}: "
        f"{total_commits} commits, "
        f"{len(contributors)} contributors, "
        f"{file_count} files, "
        f"{total_size} bytes, "
        f"{repo_age_days} days old, "
        f"{active_branch_count} branches, "
        f"last commit on {last_commit_date}."
    )


def get_repo_object(repo_dir):
    """
    Retrieve the Git repository object using GitPython.

    :param repo_dir: Path to the repository directory.
    :return: Repo object or None if the repository cannot be accessed.
    """
    try:
        repo_obj = Repo(repo_dir)
        return repo_obj
    except InvalidGitRepositoryError:
        logger.error(f"The directory {repo_dir} is not a valid Git repository.")
    except GitCommandError as e:
        logger.error(f"Git command error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None


if __name__ == "__main__":
    # Hardcoded values for standalone execution
    repo_slug = "WebGoat"
    repo_id = "WebGoat"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug

    repo = MockRepo(repo_id, repo_slug)

    # Define the path to the cloned repository
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create a session and run metrics calculation
    session = Session()
    try:
        logger.info(f"Running metrics calculation for hardcoded repo_id: {repo.repo_id}, repo_slug: {repo.repo_slug}")
        result = run_gitlog_analysis(repo_dir, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone metrics calculation result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone metrics calculation: {e}")
    finally:
        session.close()
        logger.info("Session closed.")