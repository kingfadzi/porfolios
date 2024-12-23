import subprocess
import json
import logging
from pathlib import Path
from sqlalchemy.dialects.postgresql import insert
from models import CheckovSarifResult
from sarif_om import SarifLog

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_checkov_sarif(repo_path, output_dir):
    """Run Checkov analysis and save SARIF output to a specified directory."""
    try:
        logger.info(f"Running Checkov on directory: {repo_path}")
        logger.info(f"SARIF output will be written to directory: {output_dir}")

        # Ensure the output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Define the SARIF file path
        sarif_file_path = Path(output_dir) / "results_sarif.sarif"

        # Run Checkov command
        result = subprocess.run(
            [
                "checkov",
                "--skip-download",
                "--directory", str(repo_path),
                "--output", "sarif",
                "--output-file", str(sarif_file_path)
            ],
            capture_output=True,
            text=True
        )

        # Log stderr for debugging
        if result.stderr.strip():
            logger.warning(f"Checkov stderr: {result.stderr.strip()}")

        # Check if the SARIF file was produced
        if not sarif_file_path.exists():
            raise RuntimeError(f"Checkov did not produce the expected SARIF file: {sarif_file_path}")

        logger.info(f"Checkov completed successfully. SARIF output written to: {sarif_file_path}")
        return sarif_file_path
    except Exception as e:
        logger.error(f"Error during Checkov execution: {e}")
        raise

def parse_sarif_file(sarif_file):
    """Read and parse the SARIF file."""
    try:
        logger.info(f"Reading SARIF file from: {sarif_file}")
        with open(sarif_file, "r") as file:
            sarif_json = json.load(file)

        # Filter unsupported keys (e.g., $schema)
        sarif_json_filtered = {k: v for k, v in sarif_json.items() if not k.startswith("$")}
        sarif_log = SarifLog(**sarif_json_filtered)

        # Validate SARIF content
        if not sarif_log.runs:
            raise ValueError("SARIF JSON contains no 'runs'.")

        logger.info(f"SARIF file successfully parsed from: {sarif_file}")
        return sarif_log
    except json.JSONDecodeError:
        logger.error(f"Failed to decode SARIF JSON from file: {sarif_file}")
        raise RuntimeError("Invalid JSON in SARIF file.")
    except Exception as e:
        logger.error(f"Error processing SARIF file: {e}")
        raise

def save_sarif_results(session, repo_id, sarif_log):
    """Save SARIF results to the database."""
    logger.info(f"Saving SARIF results for repo_id: {repo_id}")
    try:
        for run in sarif_log.runs:
            tool = run.tool.driver
            rules = {rule.id: rule for rule in tool.rules or []}

            for result in run.results or []:
                rule_id = result.rule_id
                rule = rules.get(rule_id, {})
                severity = rule.properties.get("severity", "UNKNOWN") if rule.properties else "UNKNOWN"
                message = result.message.text if result.message else "No message provided"

                for location in result.locations or []:
                    physical_location = location.physical_location
                    artifact_location = physical_location.artifact_location
                    region = physical_location.region
                    file_path = artifact_location.uri if artifact_location else "N/A"
                    start_line = region.start_line if region else -1
                    end_line = region.end_line if region else -1

                    session.execute(
                        insert(CheckovSarifResult).values(
                            repo_id=repo_id,
                            rule_id=rule_id,
                            rule_name=rule.name or "No name",
                            severity=severity,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            message=message
                        ).on_conflict_do_update(
                            index_elements=["repo_id", "rule_id", "file_path", "start_line", "end_line"],
                            set_={
                                "rule_name": rule.name or "No name",
                                "severity": severity,
                                "message": message
                            }
                        )
                    )
        session.commit()
        logger.info(f"SARIF results successfully saved for repo_id: {repo_id}")
    except Exception as e:
        logger.error(f"Error saving SARIF results to the database for repo_id {repo_id}: {e}")
        raise

if __name__ == "__main__":
    import os
    from models import Session

    # Hardcoded values for standalone execution
    repo_slug = "halo"
    repo_id = "halo"
    repo_dir = "/tmp/halo"
    output_dir = "checkov_output"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id, repo_slug)

    # Initialize database session
    session = Session()

    try:
        logger.info(f"Starting standalone Checkov analysis for mock repo_id: {repo.repo_id}")
        sarif_file = run_checkov_sarif(repo_dir, output_dir)
        sarif_log = parse_sarif_file(sarif_file)
        save_sarif_results(session, repo.repo_id, sarif_log)
        logger.info(f"Standalone Checkov analysis completed successfully for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Error during standalone Checkov analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
