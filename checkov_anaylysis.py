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

# Database setup
def setup_database(db_url):
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session()

# Run Checkov analysis with enhanced debugging
def run_checkov(repo_path):
    result = subprocess.run(
        ["checkov", "--skip-download", "--directory", str(repo_path), "--quiet", "--output", "json"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Checkov failed with return code: {result.returncode}")
        print(f"Checkov stderr: {result.stderr.strip()}")
        print(f"Checkov stdout: {result.stdout.strip()}")
        raise RuntimeError(f"Checkov analysis failed: {result.stderr.strip()}")

    if not result.stdout.strip():
        print("Checkov output is empty.")
        raise RuntimeError("Checkov returned no data.")

    # Parse JSON output
    try:
        checkov_output = json.loads(result.stdout)
        summary = checkov_output.get("summary", {})
        print(f"Checkov Summary: {summary}")  # Debugging: Print summary

        if summary.get("failed", 0) > 0:
            print(f"Checkov found {summary['failed']} failed checks.")
        elif summary.get("passed", 0) == 0:
            print("No checks passed in Checkov. Please verify the configuration.")
        return checkov_output
    except json.JSONDecodeError as e:
        print("Failed to parse Checkov JSON output.")
        print(f"Raw stdout: {result.stdout}")
        raise e

# Save Checkov results to database with upsert
def save_checkov_results(session, repo_id, results):
    for check in results['results']['failed_checks']:
        session.execute(
            insert(CheckovResult).values(
                repo_id=repo_id,
                resource=check['resource'],
                check_name=check['check_name'],
                check_result=check['check_result'],
                severity=check['severity']
            ).on_conflict_do_update(
                index_elements=["repo_id", "resource", "check_name"],  # Matches the unique constraint
                set_={
                    "check_result": check['check_result'],
                    "severity": check['severity']
                }
            )
        )
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
