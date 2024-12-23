import subprocess
import os
import logging
from datetime import datetime
from models import Session, RepoMetrics
from sqlalchemy.dialects.postgresql import insert

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_lizard_analysis(repo_dir, repo, session):
    """Run lizard to analyze code complexity and persist the results."""
    logger.info(f"Starting lizard analysis for repository: {repo.repo_name} (ID: {repo.repo_id})")
    lizard_output_file = f"{repo_dir}/lizard_output.txt"

    try:
        subprocess.run(
            f"lizard {repo_dir} > {lizard_output_file}",
            shell=True,
            check=True
        )
        logger.info(f"lizard analysis completed successfully. Output file: {lizard_output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running lizard for repository {repo.repo_name}: {e}")
        raise RuntimeError(f"lizard analysis failed for {repo.repo_name}: {e}")

    if os.path.exists(lizard_output_file):
        with open(lizard_output_file, 'r') as f:
            for line in f:
                # Parse the output line here (mocking as example)
                logger.debug(f"Lizard raw output: {line.strip()}")
                # Store metrics as an example (you would parse the actual metrics here)
                session.execute(
                    insert(RepoMetrics).values(
                        repo_id=repo.repo_id,
                        metric_type="lizard",
                        metric_key="example_metric",
                        metric_value=1.0  # Replace with parsed metric value
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "metric_type", "metric_key"],
                        set_={"metric_value": 1.0, "updated_at": datetime.utcnow()}  # Replace with parsed value
                    )
                )
            session.commit()
    else:
        raise FileNotFoundError(f"lizard output file not found: {lizard_output_file}")

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
        run_lizard_analysis(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during lizard analysis: {e}")
    finally:
        session.close()
