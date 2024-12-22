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
    file = Column(Text)
    function = Column(Text)
    nloc = Column(Integer)
    complexity = Column(Integer)
    tokens = Column(Integer)

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
    reader = csv.DictReader(csv_data)
    parsed_results = []
    for row in reader:
        parsed_results.append({
            "file": row.get("filename", ""),
            "function": row.get("function_name", ""),
            "nloc": int(row.get("nloc", 0)),
            "complexity": int(row.get("cyclomatic_complexity", 0)),
            "tokens": int(row.get("token_count", 0))
        })
    return parsed_results

# Save Lizard results to database with upsert
def save_lizard_results(session, repo_id, results):
    for record in results:
        session.execute(
            insert(LizardMetric).values(
                repo_id=repo_id,
                file=record["file"],
                function=record["function"],
                nloc=record["nloc"],
                complexity=record["complexity"],
                tokens=record["tokens"]
            ).on_conflict_do_update(
                index_elements=["repo_id", "file", "function"],  # Matches the unique constraint
                set_={
                    "nloc": record["nloc"],
                    "complexity": record["complexity"],
                    "tokens": record["tokens"]
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

# Run Checkov analysis
def run_checkov(repo_path):
    result = subprocess.run(["checkov", "--directory", str(repo_path), "--quiet", "--output", "json"], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"Checkov analysis failed: {result.stderr.strip()}")
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
    lizard_results = run_lizard(repo_path)
    save_lizard_results(session, repo_id, lizard_results)

    print("Running cloc...")
    cloc_results = run_cloc(repo_path)
    save_cloc_results(session, repo_id, cloc_results)

    print("Running Checkov...")
    checkov_results = run_checkov(repo_path)
    save_checkov_results(session, repo_id, checkov_results)

    print("Analysis complete. Results saved to database.")
