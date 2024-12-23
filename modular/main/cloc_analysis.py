import subprocess
import json
from sqlalchemy.dialects.postgresql import insert
import logging
from models import Session, ClocMetric

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_cloc_analysis(repo_dir, repo, session):
    """Run cloc analysis and persist results."""
    logger.info(f"Starting cloc analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        logger.error(f"Repository directory does not exist: {repo_dir}")
        raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

    logger.debug(f"Repository directory found: {repo_dir}")

    try:
        logger.info(f"Executing cloc command in directory: {repo_dir}")
        result = subprocess.run(["cloc", "--json", str(repo_dir)], capture_output=True, text=True, check=True)
        logger.debug(f"cloc command completed successfully for repo_id: {repo.repo_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"cloc command failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
        raise RuntimeError("cloc analysis failed.")

    # Parse the cloc output
    if not result.stdout.strip():
        logger.error(f"No output from cloc command for repo_id: {repo.repo_id}")
        raise RuntimeError("cloc analysis returned no data.")

    logger.info(f"Parsing cloc output for repo_id: {repo.repo_id}")
    try:
        cloc_data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding cloc JSON output for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("Failed to parse cloc JSON output.")

    # Persist results to the database
    logger.info(f"Saving cloc results to the database for repo_id: {repo.repo_id}")
    try:
        save_cloc_results(session, repo.repo_id, cloc_data)
        logger.info(f"Successfully saved cloc results for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Error saving cloc results for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("Failed to save cloc results.")

def save_cloc_results(session, repo_id, results):
    """Save cloc results to the database."""
    logger.debug(f"Processing cloc results for repo_id: {repo_id}")
    for language, metrics in results.items():
        if language == "header":
            logger.debug(f"Skipping header in cloc results for repo_id: {repo_id}")
            continue

        logger.debug(
            f"Saving metrics for language: {language} - "
            f"Files: {metrics['nFiles']}, Blank: {metrics['blank']}, "
            f"Comment: {metrics['comment']}, Code: {metrics['code']}"
        )

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
    logger.debug(f"Cloc results committed to the database for repo_id: {repo_id}")


if __name__ == "__main__":
    import os
    import logging

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Hardcoded values for standalone execution
    repo_slug = "example-repo"
    repo_id = "example-repo-id"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = f"/mnt/tmpfs/cloned_repositories/{repo.repo_slug}"

    # Create a session and run cloc analysis
    session = Session()
    try:
        logger.info(f"Starting standalone cloc analysis for mock repo_id: {repo.repo_id}")
        run_cloc_analysis(repo_dir, repo, session)
        logger.info(f"Standalone cloc analysis completed successfully for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Error during standalone cloc analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
