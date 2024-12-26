import os
import subprocess  # Importing subprocess for running shell commands
import json
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, CheckovSummary, CheckovFiles, CheckovChecks
from modular.timer_decorator import log_time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@log_time
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

        # logger.debug(f"Checkov stdout:\n{result.stdout}")
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
        # Normalize checkov_data to always be a list
        if isinstance(checkov_data, dict):
            logger.debug(f"Checkov data for repo_id {repo_id} is a single item. Converting to list.")
            checkov_data = [checkov_data]
        elif not isinstance(checkov_data, list):
            logger.warning(f"Checkov data for repo_id {repo_id} is neither a list nor a dictionary.")
            logger.warning(f"Received Checkov data:\n{json.dumps(checkov_data, indent=2)}")
            return  # Gracefully exit if data is not in an expected format

        # Check if there's no valid data
        if not checkov_data:
            logger.warning(f"No Checkov data found for repo_id {repo_id}.")
            return  # Exit gracefully if no data is present

        # Process each item in the list
        processed_count = 0
        for item in checkov_data:
            check_type = item.get("check_type")
            if not check_type:
                logger.warning(f"No IaC components found for repo_id {repo_id}. Checkov data:\n{json.dumps(item, indent=2)}")
                continue  # Skip this item but continue processing others

            logger.info(f"Processing check_type: {check_type}")
            save_checkov_results(session, repo_id, check_type, item)
            processed_count += 1

        if processed_count == 0:
            logger.warning(f"No actionable Checkov data was processed for repo_id {repo_id}. Checkov data:\n{json.dumps(checkov_data, indent=2)}")
        else:
            logger.info(f"Successfully processed {processed_count} Checkov data items for repo_id {repo_id}.")

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
        logger.debug(f"Summary data: {summary}")
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

        # Save file data
        files = results.get("results", {}).get("files", [])
        logger.debug(f"File data: {files}")
        processed_files = set()
        for check in results.get("results", {}).get("passed_checks", []) + results.get("results", {}).get("failed_checks", []):
            file_path = check.get("file_path")
            file_abs_path = check.get("file_abs_path")
            if file_path and file_path not in processed_files:
                logger.debug(f"Inserting file data: repo_id={repo_id}, check_type={check_type}, file_path={file_path}, file_abs_path={file_abs_path}")
                session.execute(
                    insert(CheckovFiles).values(
                        repo_id=repo_id,
                        check_type=check_type,
                        file_path=file_path,
                        file_abs_path=file_abs_path,
                        resource_count=1,  # Example logic; modify if needed
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "check_type", "file_path"],
                        set_={
                            "file_abs_path": file_abs_path,
                            "resource_count": 1,  # Update logic as required
                        },
                    )
                )
                processed_files.add(file_path)

        # Save individual checks
        checks = results.get("results", {}).get("passed_checks", []) + results.get("results", {}).get("failed_checks", [])
        # logger.debug(f"Check data: {checks}")
        for check in checks:
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
                    set_={
                        "file_path": check.get("file_path"),
                        "check_name": check.get("check_name"),
                        "result": check.get("check_result", {}).get("result"),
                        "severity": check.get("severity"),
                        "resource": check.get("resource"),
                        "guideline": check.get("guideline"),
                        "start_line": check.get("code_block", [[None]])[0][0] if check.get("code_block") else None,
                        "end_line": check.get("code_block", [[None]])[-1][0] if check.get("code_block") else None,
                    },
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
