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

    # Run Checkov command
    output_file = os.path.join(repo_dir, "checkov_results.json")
    log_file = os.path.join(repo_dir, "checkov_analysis.log")
    try:
        with open(log_file, "w") as log_fh:
            result = subprocess.run(
                [
                    "checkov",
                    "--directory", str(repo_dir),
                    "--output", "json",
                    "--output-file-path", output_file,
                    "--skip-download"
                ],
                stdout=log_fh,
                stderr=log_fh,
                check=False
            )
            logger.debug(f"Checkov command finished with return code {result.returncode} for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Failed to execute Checkov for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("Checkov analysis failed.") from e

    # Check return code
    if result.returncode != 0:
        logger.error(f"Checkov analysis failed for repo_id {repo.repo_id}. Check logs at: {log_file}")
        raise RuntimeError("Checkov analysis returned a non-zero exit code.")

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
    Save Checkov results to the database in CheckovFiles, CheckovChecks, and CheckovSummary tables.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}")

    try:
        # Save summary
        summary = results.get("summary", {})
        session.execute(
            insert(CheckovSummary).values(
                repo_id=repo_id,
                passed=summary.get("passed", 0),
                failed=summary.get("failed", 0),
                skipped=summary.get("skipped", 0),
                parsing_errors=summary.get("parsing_errors", 0)
            ).on_conflict_do_update(
                index_elements=["repo_id"],
                set_={
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                    "parsing_errors": summary.get("parsing_errors", 0)
                }
            )
        )

        # Save files and checks
        for check_type, check_data in results.get("results", {}).items():
            for check in check_data.get("checks", []):
                file_path = check.get("file_path")
                file_abs_path = check.get("file_abs_path")
                file_type = check.get("file_type", check_type)  # Derive file type from check_type
                resource_count = check.get("resource_count", 0)

                # Save file details
                session.execute(
                    insert(CheckovFiles).values(
                        file_path=file_path,
                        file_abs_path=file_abs_path,
                        file_type=file_type,
                        resource_count=resource_count
                    ).on_conflict_do_update(
                        index_elements=["file_path"],
                        set_={
                            "file_abs_path": file_abs_path,
                            "file_type": file_type,
                            "resource_count": resource_count
                        }
                    )
                )

                # Save individual checks
                for result in check.get("results", []):
                    session.execute(
                        insert(CheckovChecks).values(
                            file_path=file_path,
                            check_id=result["check_id"],
                            check_name=result["check_name"],
                            result=result["result"],
                            resource=result.get("resource"),
                            guideline=result.get("guideline"),
                            start_line=result.get("start_line"),
                            end_line=result.get("end_line")
                        ).on_conflict_do_update(
                            index_elements=["file_path", "check_id", "start_line", "end_line"],
                            set_={
                                "check_name": result["check_name"],
                                "result": result["result"],
                                "resource": result.get("resource"),
                                "guideline": result.get("guideline")
                            }
                        )
                    )

        session.commit()
        logger.debug(f"Checkov results committed to the database for repo_id: {repo_id}")

    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}")
        raise


if __name__ == "__main__":
    # Hardcoded values for a standalone test
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
