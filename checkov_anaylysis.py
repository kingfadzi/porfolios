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

# Run Checkov analysis and save SARIF output to a directory
def run_checkov_sarif(repo_path, output_dir):
    try:
        print(f"Running Checkov on directory: {repo_path}")
        print(f"SARIF output will be written to directory: {output_dir}")

        # Ensure the output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Run Checkov and write output to the directory
        result = subprocess.run(
            ["checkov", "--skip-download", "--directory", str(repo_path), "--output", "sarif", "--output-file", str(output_dir)],
            capture_output=True,
            text=True
        )

        # Log stderr for debugging
        if result.stderr.strip():
            print(f"Checkov stderr: {result.stderr.strip()}")

        # Check for the expected SARIF file inside the directory
        sarif_file = Path(output_dir) / "results_sarif.sarif"
        if not sarif_file.exists():
            raise RuntimeError(f"Checkov did not produce the expected SARIF file: {sarif_file}")

        print(f"Checkov completed successfully. SARIF output written to: {sarif_file}")
        return sarif_file
    except Exception as e:
        print(f"Error during Checkov execution: {e}")
        raise

# Read SARIF JSON from file and parse
def parse_sarif_file(sarif_file):
    try:
        print(f"Reading SARIF file from: {sarif_file}")
        with open(sarif_file, "r") as file:
            sarif_json = json.load(file)

        # Remove unsupported keys (e.g., $schema)
        sarif_json_filtered = {k: v for k, v in sarif_json.items() if not k.startswith("$")}

        # Parse the filtered SARIF JSON into a SarifLog object
        sarif_log = SarifLog(**sarif_json_filtered)

        # Validate that runs exist
        if not sarif_log.runs:
            raise ValueError("SARIF JSON is valid but contains no 'runs'.")

        print(f"SARIF file successfully parsed from: {sarif_file}")
        return sarif_log
    except json.JSONDecodeError:
        print(f"Failed to decode SARIF JSON from file: {sarif_file}")
        raise RuntimeError(f"Invalid JSON in file: {sarif_file}")
    except Exception as e:
        print(f"Error while processing SARIF file: {e}")
        raise


# Save SARIF results to the database
from sarif_om import SarifLog, Run

def save_sarif_results(session, repo_id, sarif_log):
    try:
        print(f"Saving SARIF results for repo_id: {repo_id} to the database.")

        # Ensure each run is wrapped in a SarifRun object
        runs = [Run(**run) if isinstance(run, dict) else run for run in sarif_log.runs]

        for run in runs:
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
        print("SARIF results successfully saved to the database.")
    except Exception as e:
        print(f"Error while saving SARIF results to the database: {e}")
        raise


if __name__ == "__main__":
    repo_path = Path("/tmp/halo")  # Path to your repository
    output_dir = "checkov_output"  # Directory to save SARIF output
    db_url = "postgresql://postgres:postgres@localhost:5432/gitlab-usage"  # PostgreSQL connection details

    session = setup_database(db_url)

    # Assume repo_id is retrieved or assigned for the repository being analyzed
    repo_id = 1  # Replace with the actual repo_id

    # Run Checkov with SARIF output
    print("Starting Checkov analysis...")
    sarif_file = run_checkov_sarif(repo_path, output_dir)

    # Parse SARIF from file
    sarif_log = parse_sarif_file(sarif_file)

    # Save results to the database
    save_sarif_results(session, repo_id, sarif_log)

    print("Analysis complete. Results saved to database.")
