import os
import re
import subprocess
import threading
from datetime import datetime, timezone
from modular.models import Session, Repository
from modular.execution_decorator import analyze_execution  # Updated decorator import
from modular.config import Config
from base_logger import BaseLogger

# Limit concurrent cloning
clone_semaphore = threading.Semaphore(10)


class CloningAnalyzer(BaseLogger):
    """
    Analyzer class for cloning repositories with class-specific logging using BaseLogger.
    """

    def __init__(self):
        self.logger = self.get_logger()

    def ensure_ssh_url(self, clone_url):
        """
        Ensure the given URL is in SSH format. GitHub URLs are assumed to be valid SSH.
        Supports Bitbucket Server and GitLab (hosted and self-hosted).
        """
        self.logger.debug(f"Processing URL: {clone_url}")

        if clone_url.startswith("https://"):
            self.logger.debug("Detected HTTPS URL format.")
            # Match Bitbucket Server URL
            bitbucket_match = re.match(r"https://(.*?)/scm/(.*?)/(.*?\.git)", clone_url)
            if bitbucket_match:
                domain, project_key, repo_slug = bitbucket_match.groups()
                self.logger.debug(
                    f"Matched Bitbucket Server URL: domain={domain}, project_key={project_key}, repo_slug={repo_slug}"
                )
                return f"ssh://git@{domain}:7999/{project_key}/{repo_slug}"

            # Match GitLab (hosted or self-hosted) URL
            gitlab_match = re.match(r"https://(.*?)/(.+?)/(.+?\.git)", clone_url)
            if gitlab_match:
                domain, group, repo_slug = gitlab_match.groups()
                self.logger.debug(
                    f"Matched GitLab URL: domain={domain}, group={group}, repo_slug={repo_slug}"
                )
                return f"ssh://git@{domain}/{group}/{repo_slug}"

            self.logger.error(f"Unsupported HTTPS URL format: {clone_url}")
            raise ValueError(f"Unsupported HTTPS URL format: {clone_url}")

        elif clone_url.startswith("ssh://"):
            self.logger.debug("Detected valid SSH URL format.")
            return clone_url  # Valid SSH, return as-is

        self.logger.error(f"Unsupported URL format: {clone_url}")
        raise ValueError(f"Unsupported URL format: {clone_url}")

    @analyze_execution(session_factory=Session, stage="Clone Repository")
    def clone_repository(self, repo, timeout_seconds=300, run_id=None):
        """
        Clone the specified repository into /mnt/tmpfs/cloned_repositories.
        Uses a semaphore to limit concurrent clones to 10.
        Logs execution details and accepts an optional run_id for tracking.
        """
        self.logger.info(f"Starting cloning for repo: {repo.repo_id}")

        base_dir = Config.CLONED_REPOSITORIES_DIR
        repo_dir = f"{base_dir}/{repo.repo_slug}"
        os.makedirs(base_dir, exist_ok=True)

        # Extract hostname for tracking
        self.set_repo_hostname(repo)

        # Ensure the URL is in SSH format
        clone_url = self.ensure_ssh_url(repo.clone_url_ssh)

        with clone_semaphore:
            try:
                # Remove any existing directory before cloning
                ssh_command = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes"
                subprocess.run(
                    f"rm -rf {repo_dir} && GIT_SSH_COMMAND='{ssh_command}' git clone {clone_url} {repo_dir}",
                    shell=True,
                    check=True,
                    timeout=timeout_seconds,
                    capture_output=True,  # Capture stdout and stderr
                    text=True,  # Decode output as text
                )
                self.logger.info(f"Successfully cloned repository '{repo.repo_name}' to {repo_dir}.")
                return repo_dir
            except subprocess.TimeoutExpired:
                error_msg = f"Cloning repository {repo.repo_name} took too long (>{timeout_seconds}s)."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            except subprocess.CalledProcessError as e:
                # Capture and log stderr for detailed error context
                error_msg = (
                    f"Error cloning repository {repo.repo_name}. "
                    f"Return code: {e.returncode}. Stderr: {e.stderr.strip()}"
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

    def set_repo_hostname(self, repo):
        """
        Extract the hostname from repo.clone_url_ssh and store it in repo.host_name.
        Handles SSH URLs for GitHub, Bitbucket, and GitLab.
        """
        clone_url = repo.clone_url_ssh
        self.logger.debug(f"Setting host_name for URL: {clone_url}")

        # Match Bitbucket Server or GitLab SSH URL
        match = re.match(r"ssh://git@([^:]+):\d*/.*", clone_url)
        if match:
            repo.host_name = match.group(1)
            self.logger.debug(f"Set host_name: {repo.host_name}")
            return

        # Match GitHub-style SSH URL
        if "github.com" in clone_url:
            repo.host_name = "github.com"
            self.logger.debug(f"Set host_name for GitHub: {repo.host_name}")
            return

        self.logger.error(f"Unsupported URL format for setting host_name: {clone_url}")
        raise ValueError(f"Unsupported URL format for setting host_name: {clone_url}")

    def cleanup_repository_directory(self, repo_dir):
        """
        Remove the cloned repository directory to free up space.
        """
        if os.path.exists(repo_dir):
            subprocess.run(f"rm -rf {repo_dir}", shell=True, check=True)
            self.logger.info(f"Cleaned up repository directory: {repo_dir}")


if __name__ == "__main__":
    session = Session()

    # Fetch a sample repository (status="NEW", just for demo)
    repositories = session.query(Repository).filter_by(status="NEW").limit(1).all()
    analyzer = CloningAnalyzer()  # Create a single instance of the analyzer

    for repo in repositories:
        repo_dir = None
        try:
            repo_dir = analyzer.clone_repository(repo, run_id="STANDALONE_RUN_001")
            print(f"Cloned repository: {repo_dir}")
        except Exception as e:
            analyzer.logger.error(f"Cloning failed: {e}")
        finally:
            if repo_dir:
                analyzer.cleanup_repository_directory(repo_dir)

    session.close()