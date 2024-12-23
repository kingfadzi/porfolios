import subprocess
import json
from sqlalchemy.dialects.postgresql import insert
import logging
from models import Session, ClocMetric

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_cloc_analysis(repo_dir, repo, session):
    """Run cloc analysis and persist results."""
    logger.info(f"Running cloc analysis for repo_id: {repo.repo_id}")
    try:
        result = subprocess.run(["cloc", "--json", str(repo_dir)], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"cloc analysis failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
        raise RuntimeError("cloc analysis failed.")

    cloc_data = json.loads(result.stdout)
    save_cloc_results(session, repo.repo_id, cloc_data)

def save_cloc_results(session, repo_id, results):
    for language, metrics in results.items():
        if language == "header":
            continue
        session.execute(
            insert(ClocMetric).values(
                repo_id=repo_id,
                language=language,
                files=metrics["nFiles"],
                blank=metrics["blank"],
                comment=metrics["comment"],
                code=metrics["code"]
            ).on_conflict_do_update(
                index_elements=["repo_id", "language"],
                set_={
                    "files": metrics["nFiles"],
                    "blank": metrics["blank"],
                    "comment": metrics["comment"],
                    "code": metrics["code"],
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
        run_cloc_analysis(repo_dir, mock_repo, session)
    except Exception as e:
        logger.error(f"Error during cloc analysis: {e}")
    finally:
        session.close()
