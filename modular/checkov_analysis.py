import os
import subprocess
import json
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, CheckovSummary, CheckovFiles, CheckovChecks

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

    # Define output directory and files
    output_dir = os.path.join(repo_dir, "checkov_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "results_json.json")
    log_file = os.path.join(output_dir, "checkov.log")

    # Run Checkov command
    try:
        logger.info(f"Executing Checkov command for repo_id: {repo.repo_id}")
        with open(log_file, "w") as log_fh:
            result = subprocess.run(
                [
                    "checkov",
                    "--directory", str(repo_dir),
                    "--output", "json",
                    "--output-file-path", output_dir,
                    "--skip-download"
                ],
                stdout=log_fh,
                stderr=log_fh,
                text=True
            )
    except subprocess.SubprocessError as e:
        logger.exception(f"Subprocess error during Checkov execution for repo_id {repo.repo_id}")
        raise RuntimeError("Checkov analysis failed.") from e

    # Validate output file
    if not os.path.exists(output_file):
        logger.error(f"Checkov did not produce the expected output file: {output_file}")
        raise RuntimeError(f"Checkov analysis failed: No output file generated. Check {log_file} for details.")

    logger.info(f"Checkov output file located at: {output_file}")
    logger.info(f"Checkov logs written to: {log_file}")

    # Parse the Checkov JSON output
    logger.info(f"Parsing Checkov output for repo_id: {repo.repo_id}")
    try:
        with open(output_file, "r") as file:
            checkov_data = json.load(file)
        if not isinstance(checkov_data, list) or not checkov_data:
            raise ValueError("Checkov returned invalid or empty data.")
        logger.info(f"Checkov output successfully parsed for repo_id: {repo.repo_id}.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing Checkov JSON output for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("Checkov analysis returned invalid data.") from e

    # Save results to the database
    save_checkov_results(session, repo.repo_id, checkov_data)
    logger.info(f"Successfully saved Checkov results for repo_id: {repo.repo_id}")


def save_checkov_results(session, repo_id, results):
    """
    Save Checkov results to the database in CheckovSummary, CheckovFiles, and CheckovChecks tables.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}")

    try:
        for item in results:
            check_type = item.get("check_type")
            summary = item.get("summary", {})

            # Save summary
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
                    }
                )
            )

            # Save files
            for check in item.get("results", {}).get("passed_checks", []) + item.get("results", {}).get("failed_checks", []):
                file_path = check.get("file_path")
                file_abs_path = check.get("file_abs_path")
                file_type = check_type

                session.execute(
                    insert(CheckovFiles).values(
                        repo_id=repo_id,
                        file_path=file_path,
                        file_abs_path=file_abs_path,
                        file_type=file_type
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "file_path"],
                        set_={
                            "file_abs_path": file_abs_path,
                            "file_type": file_type
                        }
                    )
                )

            # Save checks
            for result_type, result_list in item.get("results", {}).items():
                for check in result_list:
                    session.execute(
                        insert(CheckovChecks).values(
                            repo_id=repo_id,
                            file_path=check.get("file_path"),
                            check_type=check_type,
                            check_id=check.get("check_id"),
                            check_name=check.get("check_name"),
                            result=result_type.upper(),
                            severity=check.get("severity"),
                            resource=check.get("resource"),
                            guideline=check.get("guideline"),
                            start_line=check.get("file_line_range", [None, None])[0],
                            end_line=check.get("file_line_range", [None, None])[1],
                        ).on_conflict_do_update(
                            index_elements=["repo_id", "file_path", "check_type", "check_id"],
                            set_={
                                "check_name": check.get("check_name"),
                                "result": result_type.upper(),
                                "severity": check.get("severity"),
                                "resource": check.get("resource"),
                                "guideline": check.get("guideline"),
                            }
                        )
                    )

        session.commit()
        logger.info(f"Checkov results successfully saved for repo_id: {repo_id}")
    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}")
        raise


if __name__ == "__main__":
    # Hardcoded values for standalone testing
    repo_slug = "sonar-metrics"
    repo_id = "sonar-metrics"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create session and run analysis
    session = Session()
    try:
        logger.info(f"Starting standalone Checkov analysis for mock repo_id: {repo.repo_id}")
        run_checkov_analysis(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during standalone Checkov analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
