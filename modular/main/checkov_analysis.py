import subprocess
import json
import logging
from pathlib import Path
from sqlalchemy.dialects.postgresql import insert
from models import Session, CheckovSarifResult

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_checkov_analysis(repo_dir, repo, session):
    """Run Checkov analysis and persist SARIF results."""
    logger.info(f"Starting Checkov analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug})")

    # Validate repository directory
    if not Path(repo_dir).exists():
        logger.error(f"Repository directory does not exist: {repo_dir}")
        raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

    logger.debug(f"Repository directory found: {repo_dir}")

    # Define output directory and SARIF file
    output_dir = Path("checkov_output") / repo.repo_slug
    sarif_file_path = output_dir / "results_sarif.sarif"

    # Run Checkov analysis
    try:
        logger.info(f"Executing Checkov analysis in directory: {repo_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "checkov",
                "--skip-download",
                "--directory", str(repo_dir),
                "--output", "sarif",
                "--output-file", str(sarif_file_path)
            ],
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"Checkov command completed successfully for repo_id: {repo.repo_id}")

        if result.stderr.strip():
            logger.warning(f"Checkov stderr: {result.stderr.strip()}")

        if not sarif_file_path.exists():
            raise RuntimeError(f"Checkov did not produce the expected SARIF file: {sarif_file_path}")

        logger.info(f"Checkov completed successfully. SARIF output written to: {sarif_file_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Checkov command failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
        raise RuntimeError("Checkov analysis failed.")

    # Parse the SARIF output
    logger.info(f"Parsing SARIF file for repo_id: {repo.repo_id}")
    try:
        with open(sarif_file_path, "r") as file:
            sarif_json = json.load(file)

        # Validate SARIF content
        if "runs" not in sarif_json or not sarif_json["runs"]:
            raise ValueError("SARIF JSON contains no 'runs'.")

        sarif_data = sarif_json["runs"][0]
        logger.info(f"SARIF file parsed successfully for repo_id: {repo.repo_id}")
    except json.JSONDecodeError:
        logger.error(f"Failed to decode SARIF JSON for repo_id: {repo.repo_id}")
        raise RuntimeError("Invalid JSON in SARIF file.")
    except Exception as e:
        logger.error(f"Error parsing SARIF file for repo_id {repo.repo_id}: {e}")
        raise RuntimeError("SARIF file processing failed.")

    # Save SARIF results to the database
    save_checkov_results(session, repo.repo_id, sarif_data)

def save_checkov_results(session, repo_id, sarif_data):
    """Save Checkov SARIF results to the database."""
    logger.info(f"Saving Checkov SARIF results for repo_id: {repo_id}")
    try:
        tool = sarif_data["tool"]["driver"]
        rules = {rule["id"]: rule for rule in tool.get("rules", [])}

        for result in sarif_data.get("results", []):
            rule_id = result.get("ruleId")
            rule = rules.get(rule_id, {})
            severity = rule.get("properties", {}).get("severity", "UNKNOWN")
            message = result.get("message", {}).get("text", "No message provided")

            for location in result.get("locations", []):
                physical_location = location.get("physicalLocation", {})
                artifact_location = physical_location.get("artifactLocation", {})
                region = physical_location.get("region", {})
                file_path = artifact_location.get("uri", "N/A")
                start_line = region.get("startLine", -1)
                end_line = region.get("endLine", -1)

                session.execute(
                    insert(CheckovSarifResult).values(
                        repo_id=repo_id,
                        rule_id=rule_id,
                        rule_name=rule.get("name", "No name"),
                        severity=severity,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        message=message
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "rule_id", "file_path", "start_line", "end_line"],
                        set_={
                            "rule_name": rule.get("name", "No name"),
                            "severity": severity,
                            "message": message
                        }
                    )
                )
        session.commit()
        logger.info(f"Checkov SARIF results successfully saved for repo_id: {repo_id}")
    except Exception as e:
        logger.error(f"Error saving Checkov SARIF results for repo_id {repo_id}: {e}")
        raise

if __name__ == "__main__":
    import os

    # Hardcoded values for standalone execution
    repo_slug = "halo"
    repo_id = "halo"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = "/tmp/halo"

    # Initialize database session
    session = Session()

    try:
        logger.info(f"Starting standalone Checkov analysis for mock repo_id: {repo.repo_id}")
        run_checkov_analysis(repo_dir, repo, session)
        logger.info(f"Standalone Checkov analysis completed successfully for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Error during standalone Checkov analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
