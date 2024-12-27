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
    :return: Success message with the number of processed items or raises an exception on failure.
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
            raise RuntimeError("Checkov analysis failed: No output file generated.")

        # Process Checkov output
        processed_items = parse_and_process_checkov_output(repo.repo_id, results_file, session)

    except Exception as e:
        logger.exception(f"Error during Checkov execution for repo_id {repo.repo_id}: {e}")
        return "Error during Checkov execution."

    # Return success message
    return f"{processed_items} items processed."


def parse_and_process_checkov_output(repo_id, checkov_output_path, session):
    """
    Parse the Checkov output and process the results.

    :param repo_id: Repository ID being analyzed.
    :param checkov_output_path: Path to the Checkov output JSON file.
    :param session: Database session for saving results.
    :return: Number of items processed.
    """
    try:
        logger.info(f"Reading Checkov output file at: {checkov_output_path}")
        with open(checkov_output_path, "r") as file:
            checkov_data = json.load(file)

        if not checkov_data:
            logger.warning(f"Checkov output is empty for repo_id {repo_id}.")
            return 0  # Return 0 if no data to process

        logger.info(f"Checkov output successfully parsed for repo_id: {repo_id}.")
        return process_checkov_data(repo_id, checkov_data, session)

    except (json.JSONDecodeError, ValueError) as e:
        error_message = f"Error parsing Checkov JSON output for repo_id {repo_id}: {e}"
        logger.error(error_message)
        return 0  # Return 0 if error occurs in parsing

    except Exception as e:
        logger.exception(f"Unexpected error processing Checkov output for repo_id {repo_id}: {e}")
        return 0  # Return 0 if an unexpected error occurs


def process_checkov_data(repo_id, checkov_data, session):
    """
    Process the parsed Checkov data for a specific repository.

    :param repo_id: Repository ID being analyzed.
    :param checkov_data: Parsed JSON data from Checkov output.
    :param session: Database session to persist the results.
    :return: Number of items processed.
    """
    try:
        # Normalize data structure
        if isinstance(checkov_data, dict):
            checkov_data = [checkov_data]
        if not isinstance(checkov_data, list):
            logger.warning(f"Unexpected Checkov data format for repo_id {repo_id}. Expected list.")
            return 0  # Return 0 if data format is unexpected

        # Process each item
        processed_count = 0
        for item in checkov_data:
            check_type = item.get("check_type")
            if not check_type:
                logger.debug(f"Skipping item without valid check_type: {item}")  # Log the item being skipped
                continue  # Skip items without a valid check_type

            logger.info(f"Processing check_type: {check_type}")  # Log the check_type being processed
            save_checkov_results(session, repo_id, check_type, item)
            processed_count += 1

        if processed_count == 0:
            logger.warning(f"No actionable Checkov data found for repo_id {repo_id}.")
            return 0  # Return 0 if no actionable data found

        logger.info(f"Successfully processed {processed_count} Checkov items for repo_id {repo_id}.")
        return processed_count

    except Exception as e:
        logger.exception(f"Error processing Checkov data for repo_id {repo_id}")
        return 0  # Return 0 if error occurs


def save_checkov_results(session, repo_id, check_type, results):
    """
    Save Checkov results to the database in CheckovFiles, CheckovChecks, and CheckovSummary tables.
    """
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

        # Save files and checks
        processed_files = set()
        checks = results.get("results", {}).get("passed_checks", []) + results.get("results", {}).get("failed_checks", [])

        for check in checks:
            file_path = check.get("file_path")
            if file_path not in processed_files:
                session.execute(
                    insert(CheckovFiles).values(
                        repo_id=repo_id,
                        check_type=check_type,
                        file_path=file_path,
                        file_abs_path=check.get("file_abs_path"),
                        resource_count=1,  # Example logic
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "check_type", "file_path"],
                        set_={"resource_count": 1}
                    )
                )
                processed_files.add(file_path)

            session.execute(
                insert(CheckovChecks).values(
                    repo_id=repo_id,
                    file_path=check.get("file_path"),
                    check_type=check_type,
                    check_id=check.get("check_id"),
                    check_name=check.get("check_name"),
                    result=check.get("check_result", {}).get("result"),
                    severity=check.get("severity"),
                    resource=check.get("resource"),
                    guideline=check.get("guideline"),
                    start_line=check.get("code_block", [[None]])[0][0] if check.get("code_block") else None,
                    end_line=check.get("code_block", [[None]])[-1][0] if check.get("code_block") else None,
                ).on_conflict_do_update(
                    index_elements=["repo_id", "file_path", "check_type", "check_id"],
                    set_={"result": check.get("check_result", {}).get("result")}
                )
            )

        session.commit()
        logger.info(f"Checkov results committed to the database for repo_id: {repo_id}, check_type: {check_type}")

    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}, check_type: {check_type}")
        raise


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
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
