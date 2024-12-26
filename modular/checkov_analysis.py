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
    logger.info(f"Starting Checkov analysis for repo_id: {repo.repo_id} "
                f"(repo_slug: {repo.repo_slug}).")

    try:
        # 1) Validate repository directory
        if not os.path.exists(repo_dir):
            logger.error(f"Repository directory does not exist: {repo_dir}")
            raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

        logger.debug(f"Repository directory found: {repo_dir}")

        # 2) Execute the Checkov command
        output_file = os.path.join(repo_dir, "results.json")
        logger.info(f"Executing Checkov command in directory: {repo_dir}")
        try:
            result = subprocess.run(
                [
                    "checkov",
                    "--directory", str(repo_dir),
                    "--skip-download",
                    "--output", "json",
                    "--output-file-path", str(output_file)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Checkov command completed successfully for repo_id: {repo.repo_id}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Checkov command failed for repo_id {repo.repo_id}. "
                         f"Return code: {e.returncode}. Stderr: {e.stderr.strip()}")
            logger.debug(f"Full exception info: ", exc_info=True)
            raise RuntimeError("Checkov analysis failed.") from e

        # 3) Parse the Checkov output
        if not os.path.exists(output_file):
            logger.error(f"No output file from Checkov command for repo_id: {repo.repo_id}")
            raise RuntimeError("Checkov analysis returned no data.")

        logger.info(f"Parsing Checkov output for repo_id: {repo.repo_id}")
        try:
            with open(output_file, "r") as f:
                checkov_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding Checkov JSON output for repo_id {repo.repo_id}: {e}")
            raise RuntimeError("Failed to parse Checkov JSON output.") from e

        # 4) Persist results to the database
        logger.info(f"Saving Checkov results to the database for repo_id: {repo.repo_id}")
        save_checkov_results(session, repo.repo_id, checkov_data)
        logger.info(f"Successfully saved Checkov results for repo_id: {repo.repo_id}")

    except Exception as e:
        logger.exception(f"An error occurred during Checkov analysis for repo_id {repo.repo_id}")
        raise


def save_checkov_results(session, repo_id, results):
    """
    Save Checkov results to the database.
    """
    logger.debug(f"Processing Checkov results for repo_id: {repo_id}")

    try:
        for check_type_data in results:
            check_type = check_type_data.get("check_type", "unknown")
            check_results = check_type_data.get("results", {})
            summary = check_type_data.get("summary", {})

            # Save file-level data
            for check in check_results.get("passed_checks", []) + check_results.get("failed_checks", []):
                session.execute(
                    insert(CheckovFiles).values(
                        file_path=check.get("file_path"),
                        file_abs_path=check.get("file_abs_path"),
                        file_type=check_type,
                        resource_count=1
                    ).on_conflict_do_update(
                        index_elements=["file_path"],
                        set_={"resource_count": 1}
                    )
                )

                # Save check data
                session.execute(
                    insert(CheckovChecks).values(
                        file_path=check.get("file_path"),
                        check_id=check.get("check_id"),
                        check_name=check.get("check_name"),
                        result=check["check_result"]["result"],
                        resource=check.get("resource"),
                        guideline=check.get("guideline"),
                        start_line=check.get("file_line_range", [0])[0],
                        end_line=check.get("file_line_range", [0])[1]
                    ).on_conflict_do_update(
                        index_elements=["file_path", "check_id", "start_line", "end_line"],
                        set_={
                            "check_name": check.get("check_name"),
                            "result": check["check_result"]["result"],
                            "guideline": check.get("guideline")
                        }
                    )
                )

            # Save summary data
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

        session.commit()
        logger.debug(f"Checkov results committed to the database for repo_id: {repo_id}")

    except Exception as e:
        logger.exception(f"Error saving Checkov results for repo_id {repo_id}")
        session.rollback()
        raise


if __name__ == "__main__":
    # Hardcoded values for standalone testing
    repo_slug = "halo"
    repo_id = "halo"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

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
