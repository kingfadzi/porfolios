import subprocess
import csv
from sqlalchemy.dialects.postgresql import insert
import logging
from models import Session, LizardMetric, LizardSummary

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_lizard_analysis(repo_dir, repo, session):
    """Run lizard analysis and persist results."""
    logger.info(f"Starting lizard analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug})")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        logger.error(f"Repository directory does not exist: {repo_dir}")
        raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

    logger.debug(f"Repository directory found: {repo_dir}")

    # Run lizard analysis command
    try:
        logger.info(f"Executing lizard command in directory: {repo_dir}")
        result = subprocess.run(["lizard", "--csv", str(repo_dir)], capture_output=True, text=True, check=True)
        logger.debug(f"Lizard command completed successfully for repo_id: {repo.repo_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Lizard command failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
        raise RuntimeError("Lizard analysis failed.")

    # Parse the lizard output
    if not result.stdout.strip():
        logger.error(f"No output from lizard command for repo_id: {repo.repo_id}")
        raise RuntimeError("Lizard analysis returned no data.")

    logger.info(f"Parsing lizard output for repo_id: {repo.repo_id}")
    csv_data = result.stdout.splitlines()
    reader = csv.DictReader(csv_data, fieldnames=[
        "nloc", "ccn", "token_count", "param", "function_length", "location",
        "file_name", "function_name", "long_name", "start_line", "end_line"
    ])
    detailed_results = []
    summary = {"total_nloc": 0, "total_ccn": 0, "total_token_count": 0, "function_count": 0}

    # Process each row of the CSV output
    for row in reader:
        if row["nloc"] == "NLOC":  # Skip header row
            logger.debug("Skipping header row in lizard results.")
            continue

        logger.debug(
            f"Processing function: {row['function_name']} in file: {row['file_name']} "
            f"with NLOC: {row['nloc']}, CCN: {row['ccn']}, Tokens: {row['token_count']}"
        )

        # Aggregate metrics for the summary
        summary["total_nloc"] += int(row["nloc"])
        summary["total_ccn"] += int(row["ccn"])
        summary["total_token_count"] += int(row["token_count"])
        summary["function_count"] += 1

        # Add the detailed result to the list
        detailed_results.append({
            "file_name": row["file_name"],
            "function_name": row["function_name"],
            "long_name": row["long_name"],
            "nloc": int(row["nloc"]),
            "ccn": int(row["ccn"]),
            "token_count": int(row["token_count"]),
            "param": int(row["param"]),
            "function_length": int(row["function_length"]),
            "start_line": int(row["start_line"]),
            "end_line": int(row["end_line"]),
        })

    # Calculate average CCN
    avg_ccn = summary["total_ccn"] / summary["function_count"] if summary["function_count"] > 0 else 0
    summary["avg_ccn"] = avg_ccn

    logger.info(f"Summary for repo_id {repo.repo_id}: "
                f"Total NLOC: {summary['total_nloc']}, Avg CCN: {summary['avg_ccn']}, "
                f"Total Tokens: {summary['total_token_count']}, Function Count: {summary['function_count']}")

    # Save detailed results and summary to the database
    save_lizard_results(session, repo.repo_id, detailed_results)
    save_lizard_summary(session, repo.repo_id, summary)

def save_lizard_results(session, repo_id, results):
    """Persist detailed lizard analysis results."""
    logger.debug(f"Saving detailed lizard metrics for repo_id: {repo_id}")
    for record in results:
        logger.debug(
            f"Saving metrics for function: {record['function_name']} in file: {record['file_name']} - "
            f"NLOC: {record['nloc']}, CCN: {record['ccn']}, Tokens: {record['token_count']}"
        )
        session.execute(
            insert(LizardMetric).values(repo_id=repo_id, **record).on_conflict_do_update(
                index_elements=["repo_id", "file_name", "function_name"],
                set_={key: record[key] for key in record if key != "repo_id"}
            )
        )
    session.commit()
    logger.debug(f"Detailed lizard metrics committed to the database for repo_id: {repo_id}")

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
    import os
    import logging

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Hardcoded values for standalone execution
    repo_slug = "halo"
    repo_id = "example-repo-id"

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
