import os
import re
import subprocess
import threading
import logging
from modular.models import Session, Repository
from modular.timer_decorator import log_time

clone_semaphore = threading.Semaphore(10)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def ensure_ssh_url(clone_url):
    if clone_url.startswith("https://"):
        match = re.match(r"https://(.*?)/scm/(.*?)/(.*?\.git)", clone_url)
        if match:
            domain, project_key, repo_slug = match.groups()
            return f"ssh://git@{domain}:7999/{project_key}/{repo_slug}"
    elif clone_url.startswith("ssh://"):
        return clone_url
    raise ValueError(f"Unsupported URL format: {clone_url}")

@log_time
def clone_repository(repo, timeout_seconds=120):
    base_dir = "/mnt/tmpfs/cloned_repositories"
    repo_dir = f"{base_dir}/{repo.repo_slug}"
    os.makedirs(base_dir, exist_ok=True)
    clone_url = ensure_ssh_url(repo.clone_url_ssh)

    with clone_semaphore:
        try:
            subprocess.run(f"rm -rf {repo_dir} && git clone {clone_url} {repo_dir}",
                           shell=True, check=True, timeout=timeout_seconds)
            return repo_dir
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Cloning repository {repo.repo_name} took too long.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error cloning repository {repo.repo_name}: {e}")

def cleanup_repository_directory(repo_dir):
    if os.path.exists(repo_dir):
        subprocess.run(f"rm -rf {repo_dir}", shell=True, check=True)

if __name__ == "__main__":
    session = Session()
    repositories = session.query(Repository).filter_by(status="NEW").limit(1).all()
    for repo in repositories:
        try:
            repo_dir = clone_repository(repo)
            print(f"Cloned repository: {repo_dir}")
        finally:
            cleanup_repository_directory(repo_dir)
    session.close()
