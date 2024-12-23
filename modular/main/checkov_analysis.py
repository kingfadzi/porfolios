import subprocess
import os
import logging
from datetime import datetime
from models import Session, RepoMetrics
from sqlalchemy.dialects.postgresql import insert

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_checkov_analysis(repo_dir, repo, session):
    """Run checkov to scan for security issues and persist the results."""
    logger.info(f"Starting checkov analysis for repository: {repo.repo_name} (ID: {repo.repo_id})")
    checkov_output_file = f"{repo_dir}/checkov_output.json"

    try:
        subprocess.run(
            f"checkov -d {repo_dir} --quiet --output json > {checkov_output_file}",
            shell=True,
            check=True
        )
        logger.info(f"checkov analysis completed successfully. Output file: {checkov_output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running checkov for repository {repo.repo_name}: {e}")
        raise RuntimeError(f"checkov analysis failed for {repo.repo_name}: {e}")

    if os.path.exists(checkov_output_file):
        with open(checkov_output_file, 'r') as f:
            import json
            data = json.load(f)
            for result in data.get("results", {}).get("failed_checks", []):
                key = result.get("check_id", "unknown")
                value = 1
                logger.debug(f"checkov result - Check ID: {key}")
                session.execute(
                    insert(RepoMetrics).values(
                        repo_id=repo.repo_id,
                        metric_type="checkov",
                        metric_key=key,
                        metric_value=value
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "metric_type", "metric_key"],
                        set_={"metric_value": value, "updated_at": datetime.utcnow()}
                    )
                )
            session.commit()
    else:
        raise FileNotFoundError(f"checkov output file not found: {checkov_output_file}")

if __name__ == "__main__":
    repo_slug = "example-repo"
    repo_id = "example-repo-id"

    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = f"/mnt/tmpfs/cloned_repositories/{repo.repo_slug}"

    session = Session()
    try:
        run_checkov_analysis(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during checkov analysis: {e}")
    finally:
        session.close()
