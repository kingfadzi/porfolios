import os
import subprocess
import json
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, ClocMetric
from modular.timer_decorator import log_time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@log_time
def run_cloc_analysis(repo_dir, repo, session):
    """
    Run cloc analysis on the given repo_dir and persist results to the database.
    """
    logger.info(f"Starting cloc analysis for repo_id: {repo.repo_id} "
                f"(repo_slug: {repo.repo_slug}).")

    try:
        # 1) Validate repository directory
        if not os.path.exists(repo_dir):
            logger.error(f"Repository directory does not exist: {repo_dir}")
            raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

        logger.debug(f"Repository directory found: {repo_dir}")

        # 2) Execute the cloc command
        logger.info(f"Executing cloc command in directory: {repo_dir}")
        try:
            result = subprocess.run(
                ["cloc", "--json", str(repo_dir)],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"cloc command completed successfully for repo_id: {repo.repo_id}")
        except subprocess.CalledProcessError as e:
            # CalledProcessError is raised when `check=True` and the command returns a non-zero exit code
            logger.error(f"cloc command failed for repo_id {repo.repo_id}. "
                         f"Return code: {e.returncode}. Stderr: {e.stderr.strip()}")
            logger.debug(f"Full exception info: ", exc_info=True)
            raise RuntimeError("cloc analysis failed.") from e

        # 3) Parse the cloc output
        stdout_str = result.stdout.strip()
        if not stdout_str:
            logger.error(f"No output from cloc command for repo_id: {repo.repo_id}")
            raise RuntimeError("cloc analysis returned no data.")

        logger.info(f"Parsing cloc output for repo_id: {repo.repo_id}")
        try:
            cloc_data = json.loads(stdout_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding cloc JSON output for repo_id {repo.repo_id}: {e}")
            logger.debug(f"cloc output that failed to parse:\n{stdout_str}")
            raise RuntimeError("Failed to parse cloc JSON output.") from e

        # 4) Persist results to the database
        logger.info(f"Saving cloc results to the database for repo_id: {repo.repo_id}")
        save_cloc_results(session, repo.repo_id, cloc_data)
        logger.info(f"Successfully saved cloc results for repo_id: {repo.repo_id}")

    except Exception as e:
        # Catch all unexpected exceptions to log a full traceback.
        logger.exception(f"An error occurred during cloc analysis for repo_id {repo.repo_id}")
        raise  # Re-raise so that the caller (Airflow) is aware of the failure.


def save_cloc_results(session, repo_id, results):
    """
    Save cloc results to the database in the ClocMetric table.
    """
    logger.debug(f"Processing cloc results for repo_id: {repo_id}")

    try:
        for language, metrics in results.items():
            if language == "header":
                logger.debug(f"Skipping header in cloc results for repo_id: {repo_id}")
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

        session.commit()
        logger.debug(f"Cloc results committed to the database for repo_id: {repo_id}")

    except Exception as e:
        # Log and re-raise any DB-related error or unexpected error
        logger.exception(f"Error saving cloc results for repo_id {repo_id}")
        raise


if __name__ == "__main__":
    # This block only runs if you execute the file directly (i.e., python your_script.py)
    # In Airflow, this block is typically not used. Airflow just imports the module and calls run_cloc_analysis.
    import logging

    # Configure logging for standalone run
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Hardcoded values for a standalone test
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
