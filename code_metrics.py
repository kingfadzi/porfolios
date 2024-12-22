from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, insert
from sqlalchemy.orm import declarative_base, sessionmaker
import subprocess
import json
from pathlib import Path

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

# Run Lizard analysis
def run_lizard(repo_path):
    result = subprocess.run(["lizard", "-ojson", str(repo_path)], capture_output=True, text=True)
    return json.loads(result.stdout)

# Run cloc analysis
def run_cloc(repo_path):
    result = subprocess.run(["cloc", "--json", str(repo_path)], capture_output=True, text=True)
    return json.loads(result.stdout)

# Run Checkov analysis
def run_checkov(repo_path):
    result = subprocess.run(["checkov", "--directory", str(repo_path), "--quiet", "--output", "json"], capture_output=True, text=True)
    return json.loads(result.stdout)

# Save Lizard results to database with upsert
def save_lizard_results(session, repo_id, results):
    for file in results['files']:
        for function in file['functions']:
            stmt = insert(LizardMetric).values(
                repo_id=repo_id,
                file=file['filename'],
                function=function['name'],
                nloc=function['nloc'],
                complexity=function['cyclomatic_complexity'],
                tokens=function['token_count']
            ).on_conflict_do_update(
                index_elements=["repo_id", "file", "function"],
                set_={
                    "nloc": stmt.excluded.nloc,
                    "complexity": stmt.excluded.complexity,
                    "tokens": stmt.excluded.tokens
                }
            )
            session.execute(stmt)
    session.commit()

# Save cloc results to database with upsert
def save_cloc_results(session, repo_id, results):
    for language, metrics in results.items():
        if language == "header":
            continue
        stmt = insert(ClocMetric).values(
            repo_id=repo_id,
            language=language,
            files=metrics['nFiles'],
            blank=metrics['blank'],
            comment=metrics['comment'],
            code=metrics['code']
        ).on_conflict_do_update(
            index_elements=["repo_id", "language"],
            set_={
                "files": stmt.excluded.files,
                "blank": stmt.excluded.blank,
                "comment": stmt.excluded.comment,
                "code": stmt.excluded.code
            }
        )
        session.execute(stmt)
    session.commit()

# Save Checkov results to database with upsert
def save_checkov_results(session, repo_id, results):
    for check in results['results']['failed_checks']:
        stmt = insert(CheckovResult).values(
            repo_id=repo_id,
            resource=check['resource'],
            check_name=check['check_name'],
            check_result=check['check_result'],
            severity=check['severity']
        ).on_conflict_do_update(
            index_elements=["repo_id", "resource", "check_name"],
            set_={
                "check_result": stmt.excluded.check_result,
                "severity": stmt.excluded.severity
            }
        )
        session.execute(stmt)
    session.commit()

if __name__ == "__main__":
    repo_path = Path("/tmp/halo")  # Replace with the path to your repo
    db_url = "postgresql://postgres:postgres@localhost:5432/gitlab-usage"  # Replace with your PostgreSQL connection details

    session = setup_database(db_url)

    # Assume repo_id is retrieved or assigned for the repository being analyzed
    repo_id = 1  # Replace with actual repo_id

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
