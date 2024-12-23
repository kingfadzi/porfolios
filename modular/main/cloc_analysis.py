import subprocess
import os
import logging
from datetime import datetime
from models import Session, RepoMetrics
from sqlalchemy.dialects.postgresql import insert

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_cloc_analysis(repo_dir, repo, session):
    """Run cloc to calculate lines of code and persist the results."""
    logger.info(f"Starting cloc analysis for repository: {repo.repo_name} (ID: {repo.repo_id})")
    cloc_output_file = f"{repo_dir}/cloc_output.json"

    try:
        subprocess.run(
            f"cloc --json {repo_dir} > {cloc_output_file}",
            shell=True,
            check=True
        )
        logger.info(f"cloc analysis completed successfully. Output file: {cloc_output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running cloc for repository {repo.repo_name}: {e}")
        raise RuntimeError(f"cloc analysis failed for {repo.repo_name}: {e}")

    if os.path.exists(cloc_output_file):
        with open(cloc_output_file, 'r') as f:
            import json
            data = json.load(f)
            for language, stats in data.items():
                if language != "header":
                    for key, value in stats.items():
                        logger.debug(f"cloc result - Language: {language}, Metric: {key}, Value: {value}")
                        session.execute(
                            insert(RepoMetrics).values(
                                repo_id=repo.repo_id,
                                metric_type="cloc",
                                metric_key=f"{language}_{key}",
                                metric_value=value
                            ).on_conflict_do_update(
                                index_elements=["repo_id", "metric_type", "metric_key"],
                                set_={"metric_value": value, "updated_at": datetime.utcnow()}
                            )
                        )
            session.commit()
    else:
        raise FileNotFoundError(f"cloc output file not found: {cloc_output_file}")

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
        run_cloc_analysis(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during cloc analysis: {e}")
    finally:
        session.close()
