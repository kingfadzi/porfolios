import json
import subprocess
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, sessionmaker
from sarif_om import SarifLog

Base = declarative_base()

# ORM Models
class CheckovSarifResult(Base):
    __tablename__ = "checkov_sarif_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, nullable=False)
    rule_id = Column(Text)  # Rule identifier (e.g., CKV_AWS_21)
    rule_name = Column(Text)  # Rule name or short description
    severity = Column(Text)  # Severity of the issue
    file_path = Column(Text)  # Path to the file
    start_line = Column(Integer)  # Start line of the issue
    end_line = Column(Integer)  # End line of the issue
    message = Column(Text)  # Detailed message from the rule

# Database setup
def setup_database(db_url):
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session()

# Run Checkov analysis and get SARIF output
def run_checkov_sarif(repo_path):
    result = subprocess.run(
        ["checkov", "--skip-download", "--directory", str(repo_path), "--output", "sarif"],
        capture_output=True,
        text=True
    )

    # Log raw output for debugging
    print(f"Raw stdout:\n{result.stdout[:500]}...")  # Truncate for readability
    print(f"Raw stderr:\n{result.stderr.strip()}")

    try:
        # Attempt to parse SARIF JSON
        sarif_log = SarifLog.from_dict(json.loads(result.stdout))

        # Validate SARIF structure
        if not sarif_log.runs:
            raise ValueError("SARIF JSON is valid but contains no 'runs'.")

        print("SARIF Output successfully parsed and validated.")
        return sarif_log
    except json.JSONDecodeError:
        print("Failed to decode SARIF JSON from Checkov.")
        print(f"Raw stdout:\n{result.stdout}")
        raise RuntimeError("Invalid JSON returned by Checkov.")
    except Exception as e:
        print("An error occurred while processing SARIF output.")
        raise e


# Parse SARIF and save results into the database
def save_sarif_results(session, repo_id, sarif_log):
    for run in sarif_log.runs:
        tool = run.tool.driver
        rules = {rule.id: rule for rule in tool.rules}  # Map rules by ID

        for result in run.results:
            rule_id = result.rule_id
            rule = rules.get(rule_id, {})
            severity = rule.properties.get("severity", "UNKNOWN") if rule.properties else "UNKNOWN"
            message = result.message.text if result.message else "No message provided"

            for location in result.locations:
                physical_location = location.physical_location
                file_path = physical_location.artifact_location.uri if physical_location.artifact_location else "N/A"
                region = physical_location.region if physical_location.region else None
                start_line = region.start_line if region else -1
                end_line = region.end_line if region else -1

                # Insert into database
                session.execute(
                    insert(CheckovSarifResult).values(
                        repo_id=repo_id,
                        rule_id=rule_id,
                        rule_name=rule.name if rule else "No name",
                        severity=severity,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        message=message
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "rule_id", "file_path", "start_line", "end_line"],
                        set_={
                            "rule_name": rule.name if rule else "No name",
                            "severity": severity,
                            "message": message
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

    # Run Checkov with SARIF output
    print("Running Checkov...")
    sarif_log = run_checkov_sarif(repo_path)
    save_sarif_results(session, repo_id, sarif_log)

    print("Analysis complete. Results saved to database.")
