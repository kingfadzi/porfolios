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

    # Run Checkov command
    output_dir = os.path.join(repo_dir, "checkov_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "results_json.json")

    try:
        logger.info(f"Executing Checkov command for repo_id: {repo.repo_id}")
        result = subprocess.run(
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

        # Log stdout and stderr for debugging purposes
        logger.debug(f"Checkov stdout:\n{result.stdout}")
        logger.debug(f"Checkov stderr:\n{result.stderr}")

        if not os.path.exists(output_file):
            logger.error(f"Checkov did not produce the expected output file: {output_file}")
            raise RuntimeError("Checkov analysis failed: No output file generated.")

        logger.info(f"Checkov output file located at: {output_file}")
    except Exception as e:
        logger.error(f"Checkov command failed for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("Checkov analysis failed.") from e

    # Parse the Checkov JSON output
    logger.info(f"Parsing Checkov output for repo_id: {repo.repo_id}")
    try:
        with open(output_file, "r") as file:
            checkov_data = json.load(file)

        if isinstance(checkov_data, list):
            logger.info(f"Checkov output is a list with {len(checkov_data)} items.")
        elif isinstance(checkov_data, dict):
            logger.info("Checkov output is a dictionary.")
        else:
            raise ValueError("Checkov returned data in an unexpected format.")

        if not checkov_data:
            raise ValueError("Checkov output is empty.")

        logger.debug(f"Checkov output sample: {json.dumps(checkov_data[:1] if isinstance(checkov_data, list) else checkov_data, indent=2)}")
        logger.info(f"Checkov output successfully parsed for repo_id: {repo.repo_id}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing Checkov JSON output for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("Checkov analysis returned invalid data.") from e

    # Save results
    logger.info(f"Saving Checkov results to the database for repo_id: {repo.repo_id}")
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
