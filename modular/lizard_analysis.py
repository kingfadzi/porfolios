import subprocess
import csv
import logging
import os
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, LizardSummary
from modular.execution_decorator import analyze_execution

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@analyze_execution(session_factory=Session, stage="Lizard Analysis")
def run_lizard_analysis(repo_dir, repo, session, run_id=None):
    """Run lizard analysis and persist only the summary results."""
    logger.info(f"Starting lizard analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug})")
    analysis_file = os.path.join(repo_dir, "analysis.txt")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)
    else:
        logger.debug(f"Repository directory found: {repo_dir}")

    # Run lizard analysis command
    logger.info(f"Executing lizard command in directory: {repo_dir}")
    try:
        # Ensure the analysis file is writable
        with open(analysis_file, "w") as outfile:
            subprocess.run(
                ["lizard", "--csv"],
                stdout=outfile,
                stderr=subprocess.PIPE,
                check=True,
                cwd=repo_dir
            )
        logger.info(f"Lizard analysis completed successfully. Output file: {analysis_file}")
    except subprocess.CalledProcessError as e:
        error_message = f"Lizard command failed for repo_id {repo.repo_id}: {e.stderr.decode().strip()}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Validate the analysis file
    if not os.path.exists(analysis_file):
        error_message = f"Language analysis file not found for repository {repo.repo_name}. Expected at: {analysis_file}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # Parse and persist the language analysis results
    logger.info(f"Parsing lizard output for repo_id: {repo.repo_id}")
    try:
        processed_metrics = parse_and_persist_lizard_results(repo.repo_id, analysis_file, session)
    except Exception as e:
        error_message = f"Error while parsing or saving analysis results for repository {repo.repo_name}: {e}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Return a comprehensive success message without the "Metrics saved for" prefix
    return (
        f"{processed_metrics['total_nloc']} total NLOC, "
        f"{processed_metrics['total_ccn']} total CCN, "
        f"{processed_metrics['total_token_count']} total tokens, "
        f"{processed_metrics['function_count']} functions, "
        f"average CCN: {processed_metrics['avg_ccn']}, "
        f"last commit on {processed_metrics['last_commit_date']}."
    )


def parse_and_persist_lizard_results(repo_id, analysis_file_path, session):
    """
    Parse the lizard analysis output and persist the summary results to the database.

    :param repo_id: Repository ID being analyzed.
    :param analysis_file_path: Path to the lizard analysis output file.
    :param session: Database session for saving results.
    :return: Dictionary containing processed summary metrics.
    """
    summary = {
        "total_nloc": 0,
        "total_ccn": 0,
        "total_token_count": 0,
        "function_count": 0,
        "avg_ccn": 0.0,
        "last_commit_date": None  # Assuming you have access to this; otherwise, remove if not applicable
    }

    try:
        logger.info(f"Reading lizard analysis file at: {analysis_file_path}")
        with open(analysis_file_path, 'r') as f:
            reader = csv.DictReader(f, fieldnames=[
                "nloc", "ccn", "token_count", "param", "function_length", "location",
                "file_name", "function_name", "long_name", "start_line", "end_line"
            ])
            for row in reader:
                if row["nloc"] == "NLOC":  # Skip header row
                    logger.debug("Skipping header row in lizard results.")
                    continue

                # Aggregate metrics for the summary
                try:
                    summary["total_nloc"] += int(row["nloc"])
                    summary["total_ccn"] += int(row["ccn"])
                    summary["total_token_count"] += int(row["token_count"])
                    summary["function_count"] += 1
                except ValueError as ve:
                    logger.warning(f"Value conversion error in row: {row} - {ve}")
                    continue

        # Calculate average CCN
        summary["avg_ccn"] = summary["total_ccn"] / summary["function_count"] if summary["function_count"] > 0 else 0.0

        logger.info(f"Summary for repo_id {repo_id}: "
                    f"Total NLOC: {summary['total_nloc']}, Avg CCN: {summary['avg_ccn']}, "
                    f"Total Tokens: {summary['total_token_count']}, Function Count: {summary['function_count']}")

        # Save summary results to the database
        save_lizard_summary(session, repo_id, summary)

        return summary

    except Exception as e:
        logger.exception(f"Error while parsing lizard results for repository ID {repo_id}: {e}")
        raise


def save_lizard_summary(session, repo_id, summary):
    """Persist lizard summary metrics."""
    logger.debug(f"Saving lizard summary metrics for repo_id: {repo_id}")
    try:
        session.execute(
            insert(LizardSummary).values(
                repo_id=repo_id,
                total_nloc=summary["total_nloc"],
                total_ccn=summary["total_ccn"],
                total_token_count=summary["total_token_count"],
                function_count=summary["function_count"],
                avg_ccn=summary["avg_ccn"]
            ).on_conflict_do_update(
                index_elements=["repo_id"],
                set_={
                    "total_nloc": summary["total_nloc"],
                    "total_ccn": summary["total_ccn"],
                    "total_token_count": summary["total_token_count"],
                    "function_count": summary["function_count"],
                    "avg_ccn": summary["avg_ccn"]
                }
            )
        )
        session.commit()
        logger.debug(f"Lizard summary metrics committed to the database for repo_id: {repo_id}")
    except Exception as e:
        logger.exception(f"Error saving lizard summary metrics for repo_id {repo_id}: {e}")
        raise


if __name__ == "__main__":
    # Hardcoded values for standalone execution
    repo_slug = "WebGoat"
    repo_id = "WebGoat"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create a session and run lizard analysis
    session = Session()
    try:
        logger.info(f"Running lizard analysis for hardcoded repo_id: {repo.repo_id}, repo_slug: {repo.repo_slug}")
        result = run_lizard_analysis(repo_dir, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone lizard analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone lizard analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
