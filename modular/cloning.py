import os
import subprocess
import threading
from modular.models import Session, Repository
from modular.execution_decorator import analyze_execution
from modular.config import Config
from base_logger import BaseLogger

clone_semaphore = threading.Semaphore(10)


class CloningAnalyzer(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger()

    @analyze_execution(session_factory=Session, stage="Clone Repository")
    def clone_repository(self, repo, timeout_seconds=300, run_id=None):
        self.logger.debug(f"Received repo object: {repo.__dict__ if hasattr(repo, '__dict__') else repo}")
        if not hasattr(repo, "repo_id"):
            raise ValueError(f"'repo_id' is missing in the provided repo object: {repo}")

        base_dir = Config.CLONED_REPOSITORIES_DIR
        repo_dir = f"{base_dir}/{repo.repo_slug}"
        os.makedirs(base_dir, exist_ok=True)

        self.set_repo_hostname(repo)
        clone_url = self.ensure_ssh_url(repo.clone_url_ssh)

        with clone_semaphore:
            try:
                ssh_command = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes"
                subprocess.run(
                    f"rm -rf {repo_dir} && GIT_SSH_COMMAND='{ssh_command}' git clone {clone_url} {repo_dir}",
                    shell=True,
                    check=True,
                    timeout=timeout_seconds,
                    capture_output=True,
                    text=True,
                )
                self.logger.info(f"Successfully cloned repository '{repo.repo_name}' to {repo_dir}.")
                return repo_dir
            except subprocess.TimeoutExpired:
                error_msg = f"Cloning repository {repo.repo_name} took too long (>{timeout_seconds}s)."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            except subprocess.CalledProcessError as e:
                error_msg = (
                    f"Error cloning repository {repo.repo_name}. "
                    f"Return code: {e.returncode}. Stderr: {e.stderr.strip()}"
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

    def ensure_ssh_url(self, clone_url):
        self.logger.debug(f"Processing URL: {clone_url}")
        if clone_url.startswith("https://"):
            domain = clone_url.replace("https://", "").split("/")[0]
            repo_path = "/".join(clone_url.replace("https://", "").split("/")[1:])
            return f"ssh://git@{domain}/{repo_path}"
        return clone_url

    def set_repo_hostname(self, repo):
        clone_url = repo.clone_url_ssh
        self.logger.debug(f"Setting host_name for URL: {clone_url}")

        match = re.match(r"ssh://git@([^:]+):\d*/.*", clone_url)
        if match:
            repo.host_name = match.group(1)
            self.logger.debug(f"Set host_name: {repo.host_name}")
            return

        if "github.com" in clone_url:
            repo.host_name = "github.com"
            self.logger.debug(f"Set host_name for GitHub: {repo.host_name}")
            return

        self.logger.error(f"Unsupported URL format for setting host_name: {clone_url}")
        raise ValueError(f"Unsupported URL format for setting host_name: {clone_url}")

    def cleanup_repository_directory(self, repo_dir):
        if os.path.exists(repo_dir):
            subprocess.run(f"rm -rf {repo_dir}", shell=True, check=True)
            self.logger.info(f"Cleaned up repository directory: {repo_dir}")

if __name__ == "__main__":
    session = Session()

    # Fetch repositories with status "NEW"
    repositories = session.query(Repository).filter_by(status="NEW").limit(1).all()
    analyzer = CloningAnalyzer()

    for repo in repositories:
        # Print details of the repo object
        print(f"Repo details: {repo.__dict__ if hasattr(repo, '__dict__') else repo}")

        repo_dir = None
        try:
            # Call the clone_repository method
            repo_dir = analyzer.clone_repository(repo, run_id="STANDALONE_RUN_001")
            print(f"Cloned repository: {repo_dir}")
        except Exception as e:
            analyzer.logger.error(f"Cloning failed: {e}")
        finally:
            if repo_dir:
                analyzer.cleanup_repository_directory(repo_dir)

    session.close()
