from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, sessionmaker
import subprocess
from pathlib import Path
import json

Base = declarative_base()

# ORM Models
class CheckovResult(Base):
    __tablename__ = "checkov_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, nullable=False)
    resource = Column(Text)
    check_name = Column(Text)
    check_result = Column(Text)
    severity = Column(Text)
    file_path = Column(Text)
    line_range = Column(Text)  # Store line range as text for simplicity

# Database setup
def setup_database(db_url):
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session()

# Run Checkov analysis
def run_checkov(repo_path):
    # Run Checkov command
    result = subprocess.run(
        ["checkov", "--skip-download", "--directory", str(repo_path), "--output", "json"],
        capture_output=True,
        text=True
    )

    # Print debugging information
    print("Raw stdout:", result.stdout)  # Debugging: Check JSON output
    print("Raw stderr:", result.stderr)  # Debugging: Check error output

    # Handle JSON output
    try:
        # Attempt to parse the JSON output
        checkov_output = json.loads(result.stdout)

        # Check summary for failed checks or parsing issues
        summary = checkov_output.get("summary", {})
        print("Checkov Summary:", summary)  # Debugging: Print summary

        # Log if there are parsing errors or failed checks
        if summary.get("failed", 0) > 0:
            print(f"Checkov found {summary['failed']} failed checks.")
        if summary.get("parsing_errors", 0) > 0:
            print(f"Checkov encountered {summary['parsing_errors']} parsing errors.")

        return checkov_output

    except json.JSONDecodeError:
        # If JSON parsing fails, log and raise an error
        print("Failed to parse Checkov JSON output.")
        print(f"Raw stdout: {result.stdout}")
        raise RuntimeError("Checkov produced invalid JSON output.")

    # Handle critical failures
    if result.returncode != 0:
        raise RuntimeError(f"Checkov command failed with return code {result.returncode}: {result.stderr.strip()}")

# Save Checkov results to the database
def save_checkov_results(session, repo_id, results):
    failed_checks = results.get("results", {}).get("failed_checks", [])
    passed_checks = results.get("results", {}).get("passed_checks", [])
    parsing_errors = results.get("results", {}).get("parsing_errors", [])

    # Insert failed checks
    for check in failed_checks:
        session.execute(
            insert(CheckovResult).values(
                repo_id=repo_id,
                resource=check["resource"],
                check_name=check["check_name"],
                check_result="FAILED",
                severity=check.get("severity", "UNKNOWN"),
                file_path=check.get("file_path", "N/A"),
                line_range=str(check.get("file_line_range", "N/A"))
            ).on_conflict_do_update(
                index_elements=["repo_id", "resource", "check_name"],  # Matches the unique constraint
                set_={
                    "check_result": "FAILED",
                    "severity": check.get("severity", "UNKNOWN"),
                    "file_path": check.get("file_path", "N/A"),
                    "line_range": str(check.get("file_line_range", "N/A"))
                }
            )
        )

    # Insert passed checks (optional, depending on your needs)
    for check in passed_checks:
        session.execute(
            insert(CheckovResult).values(
                repo_id=repo_id,
                resource=check["resource"],
                check_name=check["check_name"],
                check_result="PASSED",
                severity="LOW",
                file_path=check.get("file_path", "N/A"),
                line_range=str(check.get("file_line_range", "N/A"))
            ).on_conflict_do_update(
                index_elements=["repo_id", "resource", "check_name"],  # Matches the unique constraint
                set_={
                    "check_result": "PASSED",
                    "file_path": check.get("file_path", "N/A"),
                    "line_range": str(check.get("file_line_range", "N/A"))
                }
            )
        )

    # Log parsing errors
    for error in parsing_errors:
        print(f"Parsing error: {error}")

    session.commit()

if __name__ == "__main__":
    repo_path = Path("/tmp/halo")  # Path to your repository
    db_url = "postgresql://postgres:postgres@localhost:5432/gitlab-usage"  # PostgreSQL connection details

    session = setup_database(db_url)

    # Assume repo_id is retrieved or assigned for the repository being analyzed
    repo_id = 1  # Replace with the actual repo_id

    # Run Checkov
    print("Running Checkov...")
    checkov_results = run_checkov(repo_path)
    save_checkov_results(session, repo_id, checkov_results)

    print("Analysis complete. Results saved to database.")
