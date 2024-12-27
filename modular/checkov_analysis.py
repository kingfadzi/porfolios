import os
import json
import logging
from subprocess import run
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, CheckovSummary, CheckovFiles, CheckovChecks
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
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

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
            error_message = f"Checkov did not produce the expected results file in {output_dir}."
            logger.error(error_message)
            raise FileNotFoundError(error_message)

        # Process Checkov output
        summary = parse_and_process_checkov_output(repo.repo_id, results_file, session)

    except Exception as e:
        error_message = f"Error during Checkov execution for repo_id {repo.repo_id}: {e}"
        logger.exception(error_message)
        raise RuntimeError(f"Checkov execution failed for repo_id {repo.repo_id}. Error: {e}")

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

        # Handle checkov_data if it's a list (as observed from previous errors)
        if isinstance(checkov_data, list):
            # Assuming the summary is inside the first item of the list
            summary = checkov_data[0].get('summary', {})
            checks_data = checkov_data[0].get('results', {}).get('failed_checks', []) + checkov_data[0].get('results', {}).get('passed_checks', [])
        else:
            # If checkov_data is a dictionary
            summary = checkov_data.get('summary', {})
            checks_data = checkov_data.get('results', {}).get('failed_checks', []) + checkov_data.get('results', {}).get('passed_checks', [])

        # Extract the summary values
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)
        parsing_errors = summary.get('parsing_errors', 0)

        # Process and save the check results into the database
        for check in checks_data:
            file_path = check.get('file_path')
            check_type = check.get('check_class')
            check_name = check.get('check_name')
            result = check.get('check_result', {}).get('result')
            check_id = check.get('check_id')

            save_checkov_results(session, repo_id, check_type, file_path, check_name, result, check_id)

        # Return summary in the desired format
        return f"Processed items: Passed: {passed}, Failed: {failed}, Skipped: {skipped}, Parsing Errors: {parsing_errors}"

    except (json.JSONDecodeError, ValueError) as e:
        error_message = f"Error parsing Checkov JSON output for repo_id {repo_id}: {e}"
        logger.error(error_message)
        raise RuntimeError(f"Failed to parse Checkov output for repo_id {repo_id}. Error: {e}")  # Raise a generic exception

    except Exception as e:
        error_message = f"Unexpected error processing Checkov output for repo_id {repo_id}: {e}"
        logger.exception(error_message)
        raise RuntimeError(f"Unexpected error processing Checkov output for repo_id {repo_id}. Error: {e}")


def save_checkov_results(session, repo_id, check_type, file_path, check_name, result, check_id):
    """
    Save Checkov results to the database in CheckovFiles, CheckovChecks, and CheckovSummary tables.
    """
    try:
        # Save summary
        session.execute(
            insert(CheckovSummary).values(
                repo_id=repo_id,
                check_type=check_type,
                passed=1 if result == 'PASS' else 0,
                failed=1 if result == 'FAIL' else 0,
                skipped=1 if result == 'SKIP' else 0,
                parsing_errors=0  # Assuming no parsing errors for each check, set to 0
            ).on_conflict_do_update(
                index_elements=["repo_id", "check_type"],
                set_={
                    "passed": 1 if result == 'PASS' else 0,
                    "failed": 1 if result == 'FAIL' else 0,
                    "skipped": 1 if result == 'SKIP' else 0,
                    "parsing_errors": 0,
                },
            )
        )

        # Save files and checks
        session.execute(
            insert(CheckovFiles).values(
                repo_id=repo_id,
                check_type=check_type,
                file_path=file_path,
                resource_count=1,  # Example logic for counting files
            ).on_conflict_do_update(
                index_elements=["repo_id", "check_type", "file_path"],
                set_={"resource_count": 1}
            )
        )

        session.execute(
            insert(CheckovChecks).values(
                repo_id=repo_id,
                file_path=file_path,
                check_type=check_type,
                check_id=check_id,
                check_name=check_name,
                result=result,
                severity=None,  # Assuming no severity available in this example
                resource=None,  # Resource is also assumed to be null
                guideline=None  # Assuming no guidelines
            ).on_conflict_do_update(
                index_elements=["repo_id", "file_path", "check_type", "check_id"],
                set_={"result": result}
            )
        )

        session.commit()
        logger.info(f"Checkov results committed to the database for repo_id: {repo_id}, check_type: {check_type}")

    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}, check_type {check_type}")
        raise  # Raise exception if saving results fails


if __name__ == "__main__":
    repo_slug = "WebGoat"
    repo_id = "WebGoat"
    repo_dir = f"/tmp/{repo_slug}"

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
