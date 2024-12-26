import os
import subprocess
import json
import logging
from sqlalchemy.dialects.postgresql import insert

from modular.models import Session, CheckovFiles, CheckovChecks, CheckovSummary

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run_checkov_analysis(repo_dir, repo, session):
    """
    Run Checkov analysis on the given repo_dir and persist results to the database.
    """
    logger.info(f"Starting Checkov analysis for repo_id: {repo.repo_id} "
                f"(repo_slug: {repo.repo_slug}).")

    try:
        # 1) Validate repository directory
        if not os.path.exists(repo_dir):
            logger.error(f"Repository directory does not exist: {repo_dir}")
            raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

        logger.debug(f"Repository directory found: {repo_dir}")

        # 2) Set up log file for Checkov
        log_file_path = os.path.join(repo_dir, "checkov_analysis.log")
        logger.info(f"Checkov logs will be written to: {log_file_path}")

        # 3) Execute the Checkov command
        logger.info(f"Executing Checkov command in directory: {repo_dir}")
        try:
            with open(log_file_path, "w") as log_file:
                result = subprocess.run(
                    ["checkov", "--skip-download", "--directory", str(repo_dir), "--output", "json"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                log_file.write(result.stdout)  # Save stdout to the log file
                log_file.write(result.stderr)  # Save stderr to the log file as well

            logger.debug(f"Checkov command completed successfully for repo_id: {repo.repo_id}")
        except subprocess.CalledProcessError as e:
            error_message = (
                f"Checkov command failed for repo_id {repo.repo_id}. "
                f"Return code: {e.returncode}. "
                f"Error output: {e.stderr.strip() if e.stderr else 'No stderr output'}. "
                f"Standard output: {e.stdout.strip() if e.stdout else 'No stdout output'}."
            )
            logger.error(error_message)
            raise RuntimeError(error_message)

        # 4) Parse the Checkov output
        stdout_str = result.stdout.strip()
        if not stdout_str:
            logger.error(f"No output from Checkov command for repo_id: {repo.repo_id}")
            raise RuntimeError("Checkov analysis returned no data.")

        logger.info(f"Parsing Checkov output for repo_id: {repo.repo_id}")
        try:
            checkov_data = json.loads(stdout_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding Checkov JSON output for repo_id {repo.repo_id}: {e}")
            logger.debug(f"Checkov output that failed to parse:\n{stdout_str}")
            raise RuntimeError("Failed to parse Checkov JSON output.") from e

        # 5) Persist results to the database
        logger.info(f"Saving Checkov results to the database for repo_id: {repo.repo_id}")
        save_checkov_results(session, repo.repo_id, checkov_data)
        logger.info(f"Successfully saved Checkov results for repo_id: {repo.repo_id}")

    except Exception as e:
        # Catch all unexpected exceptions to log a full traceback.
        logger.exception(f"An error occurred during Checkov analysis for repo_id {repo.repo_id}")
        raise  # Re-raise so that the caller (Airflow) is aware of the failure.


def save_checkov_results(session, repo_id, results):
    """
    Save Checkov results to the database in CheckovFiles, CheckovChecks, and CheckovSummary tables.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}")

    try:
        # Save summary
        summary = results.get("summary", {})
        session.execute(
            insert(CheckovSummary).values(
                repo_id=repo_id,
                passed=summary.get("passed", 0),
                failed=summary.get("failed", 0),
                skipped=summary.get("skipped", 0),
                parsing_errors=summary.get("parsing_errors", 0)
            ).on_conflict_do_update(
                index_elements=["repo_id"],
                set_={
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                    "parsing_errors": summary.get("parsing_errors", 0)
                }
            )
        )

        # Save files and checks
        for check_type in results.get("results", {}):
            for check in results["results"][check_type].get("checks", []):
                file_path = check.get("file_path")
                file_abs_path = check.get("file_abs_path")
                file_type = check.get("file_type", check_type)  # Derive file type from check_type
                resource_count = check.get("resource_count", 0)

                # Save file details
                session.execute(
                    insert(CheckovFiles).values(
                        file_path=file_path,
                        file_abs_path=file_abs_path,
                        file_type=file_type,
                        resource_count=resource_count
                    ).on_conflict_do_update(
                        index_elements=["file_path"],
                        set_={
                            "file_abs_path": file_abs_path,
                            "file_type": file_type,
                            "resource_count": resource_count
                        }
                    )
                )

                # Save individual checks
                for result in check.get("results", []):
                    session.execute(
                        insert(CheckovChecks).values(
                            file_path=file_path,
                            check_id=result["check_id"],
                            check_name=result["check_name"],
                            result=result["result"],
                            resource=result.get("resource"),
                            guideline=result.get("guideline"),
                            start_line=result.get("start_line"),
                            end_line=result.get("end_line")
                        ).on_conflict_do_update(
                            index_elements=["file_path", "check_id", "start_line", "end_line"],
                            set_={
                                "check_name": result["check_name"],
                                "result": result["result"],
                                "resource": result.get("resource"),
                                "guideline": result.get("guideline")
                            }
                        )
                    )

        session.commit()
        logger.debug(f"Checkov results committed to the database for repo_id: {repo_id}")

    except Exception as e:
        # Log and re-raise any DB-related error or unexpected error
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}")
        raise


if __name__ == "__main__":
    # Hardcoded values for a standalone test
    repo_slug = "halo"
    repo_id = "halo"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create a session and run Checkov analysis
    session = Session()
    try:
        logger.info(f"Starting standalone Checkov analysis for mock repo_id: {repo.repo_id}")
        run_checkov_analysis(repo_dir, repo, session)
        logger.info(f"Standalone Checkov analysis completed successfully for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Error during standalone Checkov analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
