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
    logger.info(f"Starting Checkov analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        logger.error(f"Repository directory does not exist: {repo_dir}")
        raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

    logger.debug(f"Repository directory found: {repo_dir}")

    # Define output directory and file
    output_dir = os.path.join(repo_dir, "checkov_results")
    output_file = os.path.join(output_dir, "results_json.json")

    # Run Checkov command
    try:
        subprocess.run(
            [
                "checkov",
                "--directory", str(repo_dir),
                "--output", "json",
                "--output-file-path", output_dir,
                "--skip-download"
            ],
            capture_output=True,
            text=True
        )
        logger.info(f"Checkov command completed for repo_id: {repo.repo_id}. Checking output file.")
    except Exception as e:
        logger.warning(f"Checkov command encountered an issue for repo_id {repo.repo_id}: {e}")

    # Validate output file
    if not os.path.isfile(output_file):
        logger.error(f"Checkov did not produce the expected output file: {output_file}")
        raise RuntimeError("Checkov analysis failed: No output file generated.")

    # Parse the Checkov JSON output
    logger.info(f"Parsing Checkov output for repo_id: {repo.repo_id}")
    try:
        with open(output_file, "r") as file:
            checkov_data = json.load(file)

        if not isinstance(checkov_data, list) or len(checkov_data) == 0:
            raise ValueError("Checkov JSON does not contain expected array of results.")

        logger.info(f"Checkov output successfully parsed for repo_id: {repo.repo_id}.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing Checkov JSON output for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("Checkov analysis returned invalid data.") from e

    # Log summary information from each check_type
    for check in checkov_data:
        if "summary" in check:
            logger.info(f"Summary for check_type {check['check_type']}: "
                        f"Total Passed: {check['summary']['passed']}, "
                        f"Total Failed: {check['summary']['failed']}, "
                        f"Resource Count: {check['summary']['resource_count']}")

    # Save results
    save_checkov_results(session, repo.repo_id, checkov_data)
    logger.info(f"Successfully saved Checkov results for repo_id: {repo.repo_id}")

def save_checkov_results(session, repo_id, results):
    """
    Save Checkov results to the database in CheckovFiles, CheckovChecks, and CheckovSummary tables.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}")

    try:
        for check_data in results:
            check_type = check_data.get("check_type", "unknown")
            summary = check_data.get("summary", {})

            # Save summary for the check type
            session.execute(
                insert(CheckovSummary).values(
                    repo_id=repo_id,
                    check_type=check_type,
                    passed=summary.get("passed", 0),
                    failed=summary.get("failed", 0),
                    skipped=summary.get("skipped", 0),
                    parsing_errors=summary.get("parsing_errors", 0)
                ).on_conflict_do_update(
                    index_elements=["repo_id", "check_type"],
                    set_={
                        "passed": summary.get("passed", 0),
                        "failed": summary.get("failed", 0),
                        "skipped": summary.get("skipped", 0),
                        "parsing_errors": summary.get("parsing_errors", 0)
                    }
                )
            )

            # Save passed and failed checks
            for result_type in ["passed_checks", "failed_checks"]:
                for check in check_data["results"].get(result_type, []):
                    session.execute(
                        insert(CheckovChecks).values(
                            repo_id=repo_id,
                            check_type=check_type,
                            check_id=check.get("check_id"),
                            check_name=check.get("check_name"),
                            result=result_type.upper(),
                            file_path=check.get("file_path"),
                            start_line=check.get("file_line_range", [None, None])[0],
                            end_line=check.get("file_line_range", [None, None])[1],
                            guideline=check.get("guideline")
                        ).on_conflict_do_update(
                            index_elements=["repo_id", "check_id", "check_type", "file_path"],
                            set_={
                                "check_name": check.get("check_name"),
                                "result": result_type.upper(),
                                "start_line": check.get("file_line_range", [None, None])[0],
                                "end_line": check.get("file_line_range", [None, None])[1],
                                "guideline": check.get("guideline")
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
    repo_slug = "sonar-metrics"
    repo_id = "sonar-metrics"

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
