import subprocess
import csv
from sqlalchemy.dialects.postgresql import insert
import logging
from models import Session, LizardMetric, LizardSummary

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_lizard_analysis(repo_dir, repo, session):
    """Run lizard analysis and persist results."""
    logger.info(f"Running lizard analysis for repo_id: {repo.repo_id}")
    try:
        result = subprocess.run(["lizard", "--csv", str(repo_dir)], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Lizard analysis failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
        raise RuntimeError("Lizard analysis failed.")

    csv_data = result.stdout.splitlines()
    reader = csv.DictReader(csv_data, fieldnames=[
        "nloc", "ccn", "token_count", "param", "function_length", "location",
        "file_name", "function_name", "long_name", "start_line", "end_line"
    ])
    detailed_results = []
    summary = {"total_nloc": 0, "total_ccn": 0, "total_token_count": 0, "function_count": 0}

    for row in reader:
        if row["nloc"] == "NLOC":
            continue  # Skip header row
        summary["total_nloc"] += int(row["nloc"])
        summary["total_ccn"] += int(row["ccn"])
        summary["total_token_count"] += int(row["token_count"])
        summary["function_count"] += 1
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

    avg_ccn = summary["total_ccn"] / summary["function_count"] if summary["function_count"] > 0 else 0
    summary["avg_ccn"] = avg_ccn

    save_lizard_results(session, repo.repo_id, detailed_results)
    save_lizard_summary(session, repo.repo_id, summary)

def save_lizard_results(session, repo_id, results):
    for record in results:
        session.execute(
            insert(LizardMetric).values(repo_id=repo_id, **record).on_conflict_do_update(
                index_elements=["repo_id", "file_name", "function_name"],
                set_={key: record[key] for key in record if key != "repo_id"}
            )
        )
    session.commit()

def save_lizard_summary(session, repo_id, summary):
    session.execute(
        insert(LizardSummary).values(repo_id=repo_id, **summary).on_conflict_do_update(
            index_elements=["repo_id"], set_=summary
        )
    )
    session.commit()

if __name__ == "__main__":
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug

    mock_repo = MockRepo(repo_id=1, repo_slug="mock-repo")
    repo_dir = "/path/to/repo"

    session = Session()
    try:
        run_lizard_analysis(repo_dir, mock_repo, session)
    except Exception as e:
        logger.error(f"Error during lizard analysis: {e}")
    finally:
        session.close()
