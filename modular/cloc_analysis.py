import os
import subprocess
import json
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, ClocMetric
from modular.execution_decorator import analyze_execution

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@analyze_execution(session_factory=Session, stage="CLOC Analysis")
def run_cloc_analysis(repo_dir, repo, session, run_id=None):
    """
    Run cloc analysis on the given repo_dir and persist results to the database.

    :param repo_dir: Directory path of the repository to be analyzed.
    :param repo: Repository object containing metadata like repo_id and repo_slug.
    :param session: Database session to persist the results.
    :param run_id: DAG run ID passed for tracking.
    :return: Success message with the number of processed languages or raises an exception on failure.
    """
    logger.info(f"Starting CLOC analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # Execute CLOC command
    try:
        logger.info(f"Executing CLOC command for repo_id: {repo.repo_id}")
        result = subprocess.run(
            ["cloc", "--json", str(repo_dir)],
            capture_output=True,
            text=True,
            check=False
        )

        # Validate output
        stdout_str = result.stdout.strip()
        if not stdout_str:
            error_message = f"No output from CLOC command for repo_id: {repo.repo_id}"
            logger.error(error_message)
            raise RuntimeError(error_message)

        logger.info(f"Parsing CLOC output for repo_id: {repo.repo_id}")
        try:
            cloc_data = json.loads(stdout_str)
        except json.JSONDecodeError as e:
            error_message = f"Error decoding CLOC JSON output for repo_id {repo.repo_id}: {e}"
            logger.error(error_message)
            raise RuntimeError(error_message)

        # Persist results to the database
        logger.info(f"Saving CLOC results to the database for repo_id: {repo.repo_id}")
        processed_languages = save_cloc_results(session, repo.repo_id, cloc_data)

    except Exception as e:
        logger.exception(f"Error during CLOC execution for repo_id {repo.repo_id}: {e}")
        raise

    # Return success message
    return f"{processed_languages} languages processed."


def save_cloc_results(session, repo_id, results):
    """
    Save CLOC results to the database in the ClocMetric table.

    :param session: Database session.
    :param repo_id: Repository ID being analyzed.
    :param results: Parsed CLOC JSON results.
    :return: Number of languages processed.
    """
    logger.debug(f"Processing CLOC results for repo_id: {repo_id}")

    try:
        processed_languages = 0
        for language, metrics in results.items():
            if language == "header":
                logger.debug(f"Skipping header in CLOC results for repo_id: {repo_id}")
                continue

            logger.debug(f"Saving metrics for language: {language} in repo_id: {repo_id}")
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
            processed_languages += 1

        session.commit()
        logger.debug(f"CLOC results committed to the database for repo_id: {repo_id}")
        return processed_languages

    except Exception as e:
        logger.exception(f"Error saving CLOC results for repo_id {repo_id}")
        raise


if __name__ == "__main__":
    repo_slug = "WebGoat"
    repo_id = "WebGoat"
    repo_dir = f"/tmp/{repo_slug}"

    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id, repo_slug)
    session = Session()

    try:
        logger.info(f"Starting standalone CLOC analysis for mock repo_id: {repo.repo_id}")
        result = run_cloc_analysis(repo_dir, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone CLOC analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone CLOC analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
