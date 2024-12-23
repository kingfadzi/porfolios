import json
import subprocess
from pathlib import Path
from sarif_om import SarifLog
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# ORM Models
class CheckovSarifResult(Base):
    __tablename__ = "checkov_sarif_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, nullable=False)
    rule_id = Column(Text)
    rule_name = Column(Text)
    severity = Column(Text)
    file_path = Column(Text)
    start_line = Column(Integer)
    end_line = Column(Integer)
    message = Column(Text)

# Database setup
def setup_database(db_url):
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session()

# Run Checkov analysis and save SARIF output to a file
def run_checkov_sarif(repo_path, output_file):
    # Run Checkov and write output directly to file
    result = subprocess.run(
        ["checkov", "--skip-download", "--directory", str(repo_path), "--output", "sarif", "--output-file", str(output_file)],
        capture_output=True,
        text=True
    )

    # Log stderr for debugging
    if result.stderr.strip():
        print(f"stderr: {result.stderr.strip()}")

    # Ensure the output file exists
    if not Path(output_file).exists():
        raise RuntimeError(f"Checkov did not produce an output file: {output_file}")

    print(f"SARIF output written to {output_file}")
    return output_file

# Read SARIF JSON from file and parse
def parse_sarif_file(output_file):
    try:
        with open(output_file, "r") as sarif_file:
            sarif_json = json.load(sarif_file)

        # Parse the SARIF file into a SarifLog object
        sarif_log = SarifLog(**sarif_json)

        # Validate that runs exist
        if not sarif_log.runs:
            raise ValueError("SARIF JSON is valid but contains no 'runs'.")

        print("SARIF Output successfully parsed.")
        return sarif_log
    except json.JSONDecodeError:
        print("Failed to decode SARIF JSON.")
        raise RuntimeError(f"Invalid JSON in file: {output_file}")
    except Exception as e:
        print(f"An error occurred while processing SARIF file: {e}")
        raise

# Save SARIF results to the database
def save_sarif_results(session, repo_id, sarif_log):
    for run in sarif_log.runs:
        tool = run.tool.driver
        rules = {rule.id: rule for rule in tool.rules}

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
    output_file = "checkov_output.sarif"  # File to save SARIF output
    db_url = "postgresql://postgres:postgres@localhost:5432/gitlab-usage"  # PostgreSQL connection details

    session = setup_database(db_url)

    # Assume repo_id is retrieved or assigned for the repository being analyzed
    repo_id = 1  # Replace with the actual repo_id

    # Run Checkov with SARIF output
    print("Running Checkov...")
    sarif_file = run_checkov_sarif(repo_path, output_file)

    # Parse SARIF from file
    sarif_log = parse_sarif_file(sarif_file)

    # Save results to the database
    save_sarif_results(session, repo_id, sarif_log)

    print("Analysis complete. Results saved to database.")
