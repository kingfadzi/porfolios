import os
import subprocess
import json
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, CheckovMetric

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run_checkov_analysis(repo_dir, repo, session):
    """
    Run Checkov analysis on the given repo_dir and persist results to the database.
    """
    logger.info(f"Starting Checkov analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    try:
        # 1) Validate repository directory
        if not os.path.exists(repo_dir):
            logger.error(f"Repository directory does not exist: {repo_dir}")
            raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

        logger.debug(f"Repository directory found: {repo_dir}")

        # 2) Define file paths for logs and output
        checkov_log_file = os.path.join(repo_dir, "checkov_analysis.log")
        output_file = os.path.join(repo_dir, "checkov_results.json")

        # 3) Execute the Checkov command
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
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            # Append stdout and stderr to the log file
            with open(checkov_log_file, "a") as log_file:
                log_file.write("\n--- STDOUT ---\n")
                log_file.write(result.stdout)
                log_file.write("\n--- STDERR ---\n")
                log_file.write(result.stderr)

        except Exception as e:
            logger.error(f"Checkov execution failed: {e}")
            raise RuntimeError("Checkov analysis failed.") from e

        # Validate Checkov command execution
        if result.returncode != 0:
            logger.error(f"Checkov command failed with return code {result.returncode}.")
            logger.error(f"Checkov stdout:\n{result.stdout.strip()}")
            logger.error(f"Checkov stderr:\n{result.stderr.strip()}")
            raise RuntimeError("Checkov analysis failed.")

        # 4) Validate output file
        if not os.path.exists(output_file):
            logger.error(f"Checkov did not produce the expected output file: {output_file}")
            raise RuntimeError("Checkov analysis failed.")

        # 5) Parse the Checkov output
        logger.info(f"Parsing Checkov output for repo_id: {repo.repo_id}")
        with open(output_file, "r") as file:
            checkov_data = json.load(file)

        # 6) Persist results to the database
        logger.info(f"Saving Checkov results to the database for repo_id: {repo.repo_id}")
        save_checkov_results(session, repo.repo_id, checkov_data)
        logger.info(f"Successfully saved Checkov results for repo_id: {repo.repo_id}")

    except Exception as e:
        logger.exception(f"An error occurred during Checkov analysis for repo_id {repo.repo_id}")
        raise


def save_checkov_results(session, repo_id, results):
    """
    Save Checkov results to the database in the CheckovMetric table.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}")

    try:
        for check_type in results:
            check_type_name = check_type.get("check_type")
            result_data = check_type.get("results", {})
            for check in result_data.get("passed_checks", []) + result_data.get("failed_checks", []):
                session.execute(
                    insert(CheckovMetric).values(
                        repo_id=repo_id,
                        file_type=check_type_name,
                        check_id=check.get("check_id"),
                        check_name=check.get("check_name"),
                        result=check["check_result"]["result"],
                        severity=check.get("severity", "UNKNOWN"),
                        file_path=check.get("file_path"),
                        start_line=check.get("file_line_range", [None, None])[0],
                        end_line=check.get("file_line_range", [None, None])[1],
                        guideline=check.get("guideline"),
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "check_id", "file_path", "start_line", "end_line"],
                        set_={
                            "check_name": check.get("check_name"),
                            "result": check["check_result"]["result"],
                            "severity": check.get("severity", "UNKNOWN"),
                            "guideline": check.get("guideline"),
                        }
                    )
                )

        session.commit()
        logger.debug(f"Checkov results committed to the database for repo_id: {repo_id}")

    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}")
        raise


if __name__ == "__main__":
    # Hardcoded values for standalone test
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
