import subprocess
import csv
import logging
import os
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, LizardSummary
from modular.timer_decorator import log_time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@log_time
def run_lizard_analysis(repo_dir, repo, session):
    """Run lizard analysis and persist only the summary results."""
    logger.info(f"Starting lizard analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug})")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        logger.error(f"Repository directory does not exist: {repo_dir}")
        # raise FileNotFoundError(f"Repository directory not found: {repo_dir}")
        return

    logger.debug(f"Repository directory found: {repo_dir}")

    # Run lizard analysis command
    try:
        logger.info(f"Executing lizard command in directory: {repo_dir}")
        result = subprocess.run(["lizard", "--csv", str(repo_dir)], capture_output=True, text=True, check=True)
        logger.debug(f"Lizard command completed successfully for repo_id: {repo.repo_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Lizard command failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
        # raise RuntimeError("Lizard analysis failed.")
        return

    # Parse the lizard output
    if not result.stdout.strip():
        logger.error(f"No output from lizard command for repo_id: {repo.repo_id}")
        # raise RuntimeError("Lizard analysis returned no data.")
        return

    logger.info(f"Parsing lizard output for repo_id: {repo.repo_id}")
    csv_data = result.stdout.splitlines()
    reader = csv.DictReader(csv_data, fieldnames=[
        "nloc", "ccn", "token_count", "param", "function_length", "location",
        "file_name", "function_name", "long_name", "start_line", "end_line"
    ])
    summary = {"total_nloc": 0, "total_ccn": 0, "total_token_count": 0, "function_count": 0}

    # Process each row of the CSV output
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
    avg_ccn = summary["total_ccn"] / summary["function_count"] if summary["function_count"] > 0 else 0
    summary["avg_ccn"] = avg_ccn

    logger.info(f"Summary for repo_id {repo.repo_id}: "
                f"Total NLOC: {summary['total_nloc']}, Avg CCN: {summary['avg_ccn']}, "
                f"Total Tokens: {summary['total_token_count']}, Function Count: {summary['function_count']}")

    # Save summary results to the database
    save_lizard_summary(session, repo.repo_id, summary)

def save_lizard_summary(session, repo_id, summary):
    """Persist lizard summary metrics."""
    logger.debug(f"Saving lizard summary metrics for repo_id: {repo_id}")
    session.execute(
        insert(LizardSummary).values(repo_id=repo_id, **summary).on_conflict_do_update(
            index_elements=["repo_id"], set_=summary
        )
    )
    session.commit()
    logger.debug(f"Lizard summary metrics committed to the database for repo_id: {repo_id}")

if __name__ == "__main__":
    # Hardcoded values for standalone execution
    repo_slug = "halo"
    repo_id = "halo"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = "/tmp/halo"

    # Create a session and run lizard analysis
    session = Session()
    try:
        logger.info(f"Starting standalone lizard analysis for mock repo_id: {repo.repo_id}")
        run_lizard_analysis(repo_dir, repo, session)
        logger.info(f"Standalone lizard analysis completed successfully for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Error during standalone lizard analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
