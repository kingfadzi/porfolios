import os
import subprocess
import json
import logging
from sqlalchemy.dialects.postgresql import insert

from modular.models import Session, CheckovResult

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run_checkov_analysis(repo_dir, repo, session):
    """
    Run Checkov analysis on the given repo_dir and persist results to the database.
    """
    logger.info(f"Starting Checkov analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        logger.error(f"Repository directory does not exist: {repo_dir}")
        raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

    logger.debug(f"Repository directory found: {repo_dir}")

    # Prepare log file for Checkov
    checkov_log_file = os.path.join(repo_dir, "checkov_analysis.log")
    output_file = os.path.join(repo_dir, "checkov_results.json")

    # Run Checkov command
    try:
        with open(checkov_log_file, "w") as log_file:
            logger.info(f"Executing Checkov command in directory: {repo_dir}. Logs will be saved to: {checkov_log_file}")
            result = subprocess.run(
                [
                    "checkov",
                    "--directory", str(repo_dir),
                    "--output", "json",
                    "--output-file-path", output_file,
                    "--skip-download"
                ],
                stdout=log_file,
                stderr=subprocess.PIPE,  # Only capture stderr for error handling
                text=True
            )
    except Exception as e:
        logger.error(f"Checkov execution failed: {e}")
        raise RuntimeError("Checkov analysis failed.") from e

    # Validate Checkov command execution
    if result.returncode != 0:
        logger.error(f"Checkov command failed with return code {result.returncode}. "
                     f"Stderr: {result.stderr.strip()}")
        raise RuntimeError("Checkov analysis failed.")

    # Validate output file
    if not os.path.exists(output_file):
        logger.error(f"Checkov did not produce the expected output file: {output_file}")
        raise RuntimeError("Checkov analysis failed.")

    # Parse the Checkov JSON output
    logger.info(f"Parsing Checkov output for repo_id: {repo.repo_id}")
    try:
        with open(output_file, "r") as file:
            checkov_data = json.load(file)
        if "summary" not in checkov_data or checkov_data["summary"].get("resource_count", 0) == 0:
            raise ValueError("Checkov did not analyze any resources or produced empty results.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing Checkov JSON output: {e}")
        raise RuntimeError("Checkov analysis returned invalid data.") from e

    # Log summary
    logger.info(f"Summary for repo_id {repo.repo_id}: "
                f"Total Passed: {checkov_data['summary']['passed']}, "
                f"Total Failed: {checkov_data['summary']['failed']}, "
                f"Resource Count: {checkov_data['summary']['resource_count']}")

    # Save results
    save_checkov_results(session, repo.repo_id, checkov_data)
    logger.info(f"Successfully saved Checkov results for repo_id: {repo.repo_id}")


def save_checkov_results(session, repo_id, results):
    """
    Save Checkov results to the database in the CheckovResult table.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}")

    try:
        for check in results["results"].get("passed_checks", []) + results["results"].get("failed_checks", []):
            session.execute(
                insert(CheckovResult).values(
                    repo_id=repo_id,
                    check_type=results["check_type"],
                    check_id=check["check_id"],
                    file_path=check["file_path"],
                    resource=check["resource"],
                    result=check["check_result"]["result"],
                    severity=check.get("severity", "UNKNOWN")
                ).on_conflict_do_update(
                    index_elements=["repo_id", "check_id", "file_path"],
                    set_={
                        "resource": check["resource"],
                        "result": check["check_result"]["result"],
                        "severity": check.get("severity", "UNKNOWN"),
                    }
                )
            )

        session.commit()
        logger.debug(f"Checkov results committed to the database for repo_id: {repo_id}")

    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}")
        raise


if __name__ == "__main__":
    # Example for standalone test
    repo_slug = "halo"
    repo_id = "halo"
    repo_dir = "/tmp/halo"

    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id, repo_slug)
    session = Session()

    try:
        run_checkov_analysis(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during Checkov analysis: {e}")
    finally:
        session.close()
