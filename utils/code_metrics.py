from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, sessionmaker
import subprocess
import csv
from pathlib import Path
import json

Base = declarative_base()

# ORM Models
class LizardMetric(Base):
    __tablename__ = "lizard_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, nullable=False)
    file_name = Column(Text)  # Updated from 'file'
    function_name = Column(Text)
    long_name = Column(Text)
    nloc = Column(Integer)
    ccn = Column(Integer)  # Cyclomatic complexity
    token_count = Column(Integer)
    param = Column(Integer)
    function_length = Column(Integer)  # Updated from 'length'
    start_line = Column(Integer)  # Updated from 'start'
    end_line = Column(Integer)  # Updated from 'end'

class LizardSummary(Base):
    __tablename__ = "lizard_summary"
    repo_id = Column(Integer, primary_key=True)  # repo_id as primary key
    total_nloc = Column(Integer)
    avg_ccn = Column(Float)
    total_token_count = Column(Integer)
    function_count = Column(Integer)

class ClocMetric(Base):
    __tablename__ = "cloc_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, nullable=False)
    language = Column(Text)
    files = Column(Integer)
    blank = Column(Integer)
    comment = Column(Integer)
    code = Column(Integer)

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

# Run Lizard analysis and parse CSV
def run_lizard(repo_path):
    result = subprocess.run(["lizard", "--csv", str(repo_path)], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"Lizard analysis failed: {result.stderr.strip()}")

    # Parse CSV output
    csv_data = result.stdout.splitlines()
    reader = csv.DictReader(csv_data, fieldnames=[
        "nloc", "ccn", "token_count", "param", "function_length", "location",
        "file_name", "function_name", "long_name", "start_line", "end_line"
    ])
    parsed_results = []
    total_nloc = total_ccn = total_token_count = function_count = 0

    for row in reader:
        # Skip the header row if present
        if row["nloc"] == "NLOC":
            continue

        # Aggregate metrics for summary
        total_nloc += int(row["nloc"])
        total_ccn += int(row["ccn"])
        total_token_count += int(row["token_count"])
        function_count += 1

        # Parse the row into a structured format
        parsed_results.append({
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

    # Compute average CCN
    avg_ccn = total_ccn / function_count if function_count > 0 else 0

    return parsed_results, {
        "total_nloc": total_nloc,
        "avg_ccn": avg_ccn,
        "total_token_count": total_token_count,
        "function_count": function_count
    }

# Save Lizard results to database with upsert
def save_lizard_results(session, repo_id, results):
    for record in results:
        session.execute(
            insert(LizardMetric).values(
                repo_id=repo_id,
                file_name=record["file_name"],
                function_name=record["function_name"],
                long_name=record["long_name"],
                nloc=record["nloc"],
                ccn=record["ccn"],
                token_count=record["token_count"],
                param=record["param"],
                function_length=record["function_length"],
                start_line=record["start_line"],
                end_line=record["end_line"]
            ).on_conflict_do_update(
                index_elements=["repo_id", "file_name", "function_name"],
                set_={
                    "long_name": record["long_name"],
                    "nloc": record["nloc"],
                    "ccn": record["ccn"],
                    "token_count": record["token_count"],
                    "param": record["param"],
                    "function_length": record["function_length"],
                    "start_line": record["start_line"],
                    "end_line": record["end_line"]
                }
            )
        )
    session.commit()

# Save Lizard summary to database with upsert
def save_lizard_summary(session, repo_id, summary):
    session.execute(
        insert(LizardSummary).values(
            repo_id=repo_id,
            total_nloc=summary["total_nloc"],
            avg_ccn=summary["avg_ccn"],
            total_token_count=summary["total_token_count"],
            function_count=summary["function_count"]
        ).on_conflict_do_update(
            index_elements=["repo_id"],  # Primary key ensures upsert behavior
            set_={
                "total_nloc": summary["total_nloc"],
                "avg_ccn": summary["avg_ccn"],
                "total_token_count": summary["total_token_count"],
                "function_count": summary["function_count"]
            }
        )
    )
    session.commit()

# Run cloc analysis
def run_cloc(repo_path):
    result = subprocess.run(["cloc", "--json", str(repo_path)], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"cloc analysis failed: {result.stderr.strip()}")
    return json.loads(result.stdout)

# Save cloc results to database with upsert
def save_cloc_results(session, repo_id, results):
    for language, metrics in results.items():
        if language == "header":
            continue
        session.execute(
            insert(ClocMetric).values(
                repo_id=repo_id,
                language=language,
                files=metrics['nFiles'],
                blank=metrics['blank'],
                comment=metrics['comment'],
                code=metrics['code']
            ).on_conflict_do_update(
                index_elements=["repo_id", "language"],  # Matches the unique constraint
                set_={
                    "files": metrics['nFiles'],
                    "blank": metrics['blank'],
                    "comment": metrics['comment'],
                    "code": metrics['code']
                }
            )
        )
    session.commit()

# Run Checkov analysis with improved debugging
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

    return json.loads(result.stdout)

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

    # Run analyses
    print("Running Lizard...")
    lizard_results, lizard_summary = run_lizard(repo_path)
    save_lizard_results(session, repo_id, lizard_results)  # Save detailed results
    save_lizard_summary(session, repo_id, lizard_summary)  # Save summary

    print("Running cloc...")
    cloc_results = run_cloc(repo_path)
    save_cloc_results(session, repo_id, cloc_results)

    print("Running Checkov...")
    checkov_results = run_checkov(repo_path)
    save_checkov_results(session, repo_id, checkov_results)

    print("Analysis complete. Results saved to database.")
