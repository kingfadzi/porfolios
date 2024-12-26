import os
import subprocess  # Importing subprocess for running shell commands
import json
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, CheckovSummary, CheckovFiles, CheckovChecks

# Configure logging
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

    # Define output directory
    output_dir = os.path.join(repo_dir, "checkov_results")
    os.makedirs(output_dir, exist_ok=True)

    # Execute Checkov command
    try:
        logger.info(f"Executing Checkov command for repo_id: {repo.repo_id}")
        result = subprocess.run(
            [
                "checkov",
                "--directory", repo_dir,
                "--output", "json",
                "--output-file-path", output_dir,
                "--skip-download"
            ],
            capture_output=True,
            text=True
        )

        logger.debug(f"Checkov stdout:\n{result.stdout}")
        logger.debug(f"Checkov stderr:\n{result.stderr}")

        # Ensure output file exists
        output_file = os.path.join(output_dir, "results_json.json")
        if not os.path.isfile(output_file):
            logger.error(f"Checkov did not produce the expected output file: {output_file}")
            raise RuntimeError("Checkov analysis failed: No output file generated.")

        # Process Checkov output
        parse_and_process_checkov_output(repo.repo_id, output_file, session)

    except Exception as e:
        logger.exception(f"Error during Checkov execution for repo_id {repo.repo_id}: {e}")
        raise


def parse_and_process_checkov_output(repo_id, checkov_output_path, session):
    """
    Parse the Checkov output and process the results.

    :param repo_id: Repository ID being analyzed.
    :param checkov_output_path: Path to the Checkov output JSON file.
    :param session: Database session for saving results.
    """
    try:
        logger.info(f"Reading Checkov output file at: {checkov_output_path}")
        with open(checkov_output_path, "r") as file:
            checkov_data = json.load(file)

        if not checkov_data:
            raise ValueError("Checkov output is empty.")

        logger.info(f"Checkov output successfully parsed for repo_id: {repo_id}.")
        process_checkov_data(repo_id, checkov_data, session)

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing Checkov JSON output for repo_id {repo_id}: {e}")
        raise RuntimeError("Invalid Checkov JSON data.") from e
    except Exception as e:
        logger.exception(f"Unexpected error processing Checkov output for repo_id {repo_id}: {e}")
        raise


def process_checkov_data(repo_id, checkov_data, session):
    """
    Process the parsed Checkov data for a specific repository.
    """
    try:
        if not isinstance(checkov_data, list):
            logger.error(f"Checkov data for repo_id {repo_id} is not a list.")
            raise ValueError("Checkov data must be a list.")

        for item in checkov_data:
            check_type = item.get("check_type")
            if not check_type:
                logger.error(f"Missing 'check_type' in Checkov data for repo_id {repo_id}: {item}")
                continue  # Skip invalid entries

            logger.debug(f"Processing check_type: {check_type}")
            save_checkov_results(session, repo_id, check_type, item)

    except Exception as e:
        logger.exception(f"Error processing Checkov data for repo_id {repo_id}")
        raise



def save_checkov_results(session, repo_id, check_type, results):
    """
    Save Checkov results to the database in CheckovFiles, CheckovChecks, and CheckovSummary tables.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}, check_type: {check_type}")
    try:
        # Save summary
        summary = results.get("summary", {})
        session.execute(
            insert(CheckovSummary).values(
                repo_id=repo_id,
                check_type=check_type,
                passed=summary.get("passed", 0),
                failed=summary.get("failed", 0),
                skipped=summary.get("skipped", 0),
                parsing_errors=summary.get("parsing_errors", 0),
            ).on_conflict_do_update(
                index_elements=["repo_id", "check_type"],
                set_={
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                    "parsing_errors": summary.get("parsing_errors", 0),
                },
            )
        )

        # Save individual checks
        checks = results.get("results", {}).get("checks", [])
        for check in checks:
            session.execute(
                insert(CheckovChecks).values(
                    repo_id=repo_id,
                    check_type=check_type,
                    check_id=check.get("check_id"),
                    result=check.get("check_result", {}).get("result"),
                    resource=check.get("resource"),
                    severity=check.get("severity"),
                    file_path=check.get("file_path"),
                ).on_conflict_do_update(
                    index_elements=["repo_id", "check_type", "check_id"],
                    set_={
                        "result": check.get("check_result", {}).get("result"),
                        "resource": check.get("resource"),
                        "severity": check.get("severity"),
                        "file_path": check.get("file_path"),
                    },
                )
            )

        session.commit()
        logger.debug(f"Checkov results committed to the database for repo_id: {repo_id}, check_type: {check_type}")
    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}, check_type: {check_type}")
        raise

if __name__ == "__main__":
    repo_slug = "sonar-metrics"
    repo_id = "sonar-metrics"
    repo_dir = f"/tmp/{repo_slug}"

    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id, repo_slug)
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
