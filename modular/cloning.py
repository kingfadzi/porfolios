import os
import re
import subprocess
import threading
import logging
from datetime import datetime, timezone
from modular.models import Session, Repository
from modular.execution_decorator import analyze_execution  # Updated decorator import

clone_semaphore = threading.Semaphore(10)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def ensure_ssh_url(clone_url):
    """
    Convert an HTTP(S)-based repository URL into an SSH-based URL if necessary.
    """
    if clone_url.startswith("https://"):
        match = re.match(r"https://(.*?)/scm/(.*?)/(.*?\.git)", clone_url)
        if match:
            domain, project_key, repo_slug = match.groups()
            return f"ssh://git@{domain}:7999/{project_key}/{repo_slug}"
    elif clone_url.startswith("ssh://"):
        return clone_url

    raise ValueError(f"Unsupported URL format: {clone_url}")

@analyze_execution(session_factory=Session, stage="Clone Repository")
def clone_repository(repo, timeout_seconds=300, run_id=None):
    """
    Clone the specified repository into /mnt/tmpfs/cloned_repositories.
    Uses a semaphore to limit concurrent clones to 10.
    Logs execution details and accepts an optional run_id for tracking.

    :param repo: Repository object containing metadata like clone_url_ssh, repo_name, and repo_slug.
    :param timeout_seconds: Maximum duration (in seconds) before the cloning times out.
    :param run_id: (Optional) DAG run ID or similar unique execution identifier for logging/tracking.
    :return: Path to the cloned repository.
    """
    base_dir = "/mnt/tmpfs/cloned_repositories"
    repo_dir = f"{base_dir}/{repo.repo_slug}"
    os.makedirs(base_dir, exist_ok=True)

    set_repo_hostname(repo)

    # Convert HTTP(S) -> SSH if needed
    clone_url = ensure_ssh_url(repo.clone_url_ssh)

    with clone_semaphore:
        try:
            # Remove any existing directory before cloning
            subprocess.run(
                f"rm -rf {repo_dir} && GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=no' git clone {clone_url} {repo_dir}",
                shell=True,
                check=True,
                timeout=timeout_seconds
            )

            return repo_dir
        except subprocess.TimeoutExpired:
            error_msg = f"Cloning repository {repo.repo_name} took too long (>{timeout_seconds}s)."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except subprocess.CalledProcessError as e:
            error_msg = f"Error cloning repository {repo.repo_name}. Return code: {e.returncode}. Stderr: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

def set_repo_hostname(repo):
    """
    Extract the hostname from repo.clone_url_ssh and store it in repo.host_name.
    Handles both HTTPS and SSH-based URLs for Bitbucket (or similar).
    """
    clone_url = repo.clone_url_ssh

    # Attempt to match https://<domain>/scm/<project_key>/<repo_slug>.git
    if clone_url.startswith("https://"):
        match = re.match(r"https://([^/]+)/scm/(.*?)/(.*?\.git)", clone_url)
        if match:
            host_name = match.group(1)
            repo.host_name = host_name
            return

    # Attempt to match ssh://git@<domain>:7999/<project_key>/<repo_slug>.git
    elif clone_url.startswith("ssh://"):
        match = re.match(r"ssh://git@([^:]+):\d+/(.*?)/(.*?\.git)", clone_url)
        if match:
            host_name = match.group(1)
            repo.host_name = host_name
            return

    raise ValueError(f"Unsupported URL format for setting host_name: {clone_url}")

def cleanup_repository_directory(repo_dir):
    """
    Remove the cloned repository directory to free up space.
    """
    if os.path.exists(repo_dir):
        subprocess.run(f"rm -rf {repo_dir}", shell=True, check=True)

if __name__ == "__main__":
    session = Session()

    # Fetch a sample repository (status="NEW", just for demo)
    repositories = session.query(Repository).filter_by(status="NEW").limit(1).all()
    for repo in repositories:
        repo_dir = None
        try:
            # Optionally provide a mock run_id if testing outside Airflow
            # e.g., run_id="STANDALONE_RUN_001"
            repo_dir = clone_repository(repo, run_id="STANDALONE_RUN_001")
            print(f"Cloned repository: {repo_dir}")
        except Exception as e:
            logger.error(f"Cloning failed: {e}")
        finally:
            if repo_dir:
                cleanup_repository_directory(repo_dir)

    session.close()
