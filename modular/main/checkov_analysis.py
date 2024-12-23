import subprocess
import json
from sqlalchemy.dialects.postgresql import insert
import logging
from models import Session, CheckovResult

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_checkov_analysis(repo_dir, repo, session):
    """Run checkov analysis and persist results."""
    logger.info(f"Running Checkov analysis for repo_id: {repo.repo_id}")
    try:
        result = subprocess.run(
            ["checkov", "--skip-download", "--directory", str(repo_dir), "--quiet", "--output", "json"],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Checkov analysis failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
        raise RuntimeError("Checkov analysis failed.")

    checkov_data = json.loads(result.stdout)
    save_checkov_results(session, repo.repo_id, checkov_data)

def save_checkov_results(session, repo_id, results):
    for check in results.get("results", {}).get("failed_checks", []):
        session.execute(
            insert(CheckovResult).values(
                repo_id=repo_id,
                resource=check["resource"],
                check_name=check["check_name"],
                check_result=check["check_result"]["result"],
                severity=check.get("severity", "unknown")
            ).on_conflict_do_update(
                index_elements=["repo_id", "resource", "check_name"],
                set_={
                    "check_result": check["check_result"]["result"],
                    "severity": check.get("severity", "unknown")
                }
            )
        )
    session.commit()

if __name__ == "__main__":
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug

    mock_repo = MockRepo(repo_id=1, repo_slug="mock-repo")
    repo_dir = "/path/to/repo"

    session = Session()
    try:
        run_checkov_analysis(repo_dir, mock_repo, session)
    except Exception as e:
        logger.error(f"Error during Checkov analysis: {e}")
    finally:
        session.close()
