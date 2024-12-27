import os
import json
import logging
from subprocess import run
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, CheckovSummary
from modular.execution_decorator import analyze_execution

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@analyze_execution(session_factory=Session, stage="Checkov Analysis")
def run_checkov_analysis(repo_dir, repo, session, run_id=None):
    """
    Run Checkov analysis on the given repo_dir and persist results to the database.

    :param repo_dir: Directory path of the repository to be scanned.
    :param repo: Repository object containing metadata like repo_id and repo_slug.
    :param session: Database session to persist the results.
    :param run_id: DAG run ID passed for tracking.
    :return: Success message with the summary of processed items or raises an exception on failure.
    """
    logger.info(f"Starting Checkov analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        raise FileNotFoundError(f"Repository directory does not exist: {repo_dir}")

    # Define output directory
    output_dir = os.path.join(repo_dir, "checkov_results")
    os.makedirs(output_dir, exist_ok=True)

    # Execute Checkov command
    try:
        logger.info(f"Executing Checkov command for repo_id: {repo.repo_id}")
        run(
            [
                "checkov",
                "--directory", repo_dir,
                "--output", "json",
                "--output-file-path", output_dir,
                "--skip-download"
            ],
            check=False,
            text=True
        )

        # Validate if the results file exists in the output directory
        results_file = os.path.join(output_dir, "results_json.json")
        if not os.path.isfile(results_file):
            raise FileNotFoundError(f"Checkov did not produce the expected results file in {output_dir}.")

        # Process Checkov output
        summary = parse_and_process_checkov_output(repo.repo_id, results_file, session)

    except Exception as e:
        error_message = f"Error during Checkov execution for repo_id {repo.repo_id}: {e}"
        logger.exception(error_message)

        # Reraise the exception so the decorator can handle it
        raise RuntimeError(error_message)

    # Return summary on success to the decorator for persistence
    return f"{summary}"


def parse_and_process_checkov_output(repo_id, checkov_output_path, session):
    """
    Parse the Checkov output and process the results.

    :param repo_id: Repository ID being analyzed.
    :param checkov_output_path: Path to the Checkov output JSON file.
    :param session: Database session for saving results.
    :return: A summary string containing the counts of passed, failed, skipped, and parsing errors.
    """
    try:
        logger.info(f"Reading Checkov output file at: {checkov_output_path}")
        with open(checkov_output_path, "r") as file:
            checkov_data = json.load(file)

        if not checkov_data:
            raise ValueError(f"Checkov output is empty for repo_id {repo_id}.")  # Raise exception if output is empty

        logger.info(f"Checkov output successfully parsed for repo_id: {repo_id}.")

        # If the output is a list of checks (i.e., IaC files were found)
        if isinstance(checkov_data, list):
            for check in checkov_data:
                check_type = check.get('check_type')
                check_summary = check.get('summary', {})

                # Extract summary for each check type
                passed = check_summary.get('passed', 0)
                failed = check_summary.get('failed', 0)
                skipped = check_summary.get('skipped', 0)
                parsing_errors = check_summary.get('parsing_errors', 0)
                resource_count = check_summary.get('resource_count', 0)

                # Persist each check summary to the database
                save_checkov_results(session, repo_id, check_type, passed, failed, skipped, parsing_errors, resource_count)

            # Return the check types found in the output
            check_types = [check.get('check_type') for check in checkov_data]
            return f"Processed check types: {', '.join(check_types)}"

        else:
            # If no IaC files were found, return the exact payload received from Checkov without modification
            return json.dumps(checkov_data)

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing Checkov JSON output for repo_id {repo_id}: {e}")
        raise RuntimeError(f"Failed to parse Checkov output for repo_id {repo_id}.")  # Raise a generic exception

    except Exception as e:
        logger.exception(f"Unexpected error processing Checkov output for repo_id {repo_id}: {e}")
        raise RuntimeError(f"Unexpected error processing Checkov output for repo_id {repo_id}.")


def save_checkov_results(session, repo_id, check_type, passed, failed, skipped, parsing_errors, resource_count):
    """
    Save Checkov results to the database in CheckovSummary table.
    """
    try:
        # Save summary to CheckovSummary
        session.execute(
            insert(CheckovSummary).values(
                repo_id=repo_id,
                check_type=check_type,
                passed=passed,
                failed=failed,
                skipped=skipped,
                parsing_errors=parsing_errors,
                resource_count=resource_count,
            ).on_conflict_do_update(
                index_elements=["repo_id", "check_type"],
                set_={
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "parsing_errors": parsing_errors,
                    "resource_count": resource_count,
                },
            )
        )

        session.commit()
        logger.info(f"Checkov summary for {check_type} committed to the database for repo_id: {repo_id}")

    except Exception as e:
        logger.exception(f"Error saving Checkov summary for repo_id {repo_id}, check_type {check_type}")
        raise  # Raise exception if saving results fails


if __name__ == "__main__":
    repo_slug = "sonar-metrics"
    repo_id = "sonar-metrics"
    repo_dir = f"/Users/fadzi/Documents/journals"

    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    # Create a mock repo object
    repo = MockRepo(repo_id=repo_id, repo_slug=repo_slug)

    # Initialize a database session
    session = Session()

    try:
        logger.info(f"Starting standalone Checkov analysis for mock repo_id: {repo.repo_id}")
        # Explicitly pass the repo object
        result = run_checkov_analysis(repo_dir, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone Checkov analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone Checkov analysis: {e}")
