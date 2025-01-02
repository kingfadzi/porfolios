import subprocess
import csv
import logging
import os
import json
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, GrypeResult
from modular.execution_decorator import analyze_execution  # Updated import
from modular.config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SYFT_CONFIG_PATH = Config.SYFT_CONFIG_PATH
GRYPE_CONFIG_PATH = Config.GRYPE_CONFIG_PATH

@analyze_execution(session_factory=Session, stage="Syft and Grype Analysis")
def run_syft_and_grype_analysis(repo_dir, repo, session, run_id=None):
    """
    Run Syft to generate SBOM and Grype to analyze vulnerabilities, saving results to the database.

    :param repo_dir: Directory path of the repository to be analyzed.
    :param repo: Repository object containing metadata like repo_id and repo_slug.
    :param session: Database session to persist the results.
    :param run_id: DAG run ID passed for tracking.
    :return: Success message with the number of vulnerabilities processed or raises an exception on failure.
    """
    logger.info(f"Starting Syft and Grype analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    # Validate repository directory
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    logger.debug(f"Repository directory validated: {repo_dir}")

    # Generate SBOM using Syft
    sbom_file_path = os.path.join(repo_dir, "sbom.json")
    logger.info(f"Generating SBOM for repo_id: {repo.repo_id} using Syft.")
    try:
        subprocess.run(
            ["syft", repo_dir, "--output", "json", "--file", sbom_file_path],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug(f"SBOM successfully generated at: {sbom_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Syft command failed for repo_id {repo.repo_id}: {e.stderr.strip()}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Analyze SBOM using Grype and write results to disk
    grype_file_path = os.path.join(repo_dir, "grype-results.json")
    logger.info(f"Analyzing SBOM with Grype for repo_id: {repo.repo_id}.")
    try:
        subprocess.run(
            ["grype", f"sbom:{sbom_file_path}",  "--output", "json", "--file", grype_file_path],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug(f"Grype results written to: {grype_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Grype command failed for repo_id {repo.repo_id}: {e.stderr.strip()}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Validate the Grype results file
    if not os.path.exists(grype_file_path):
        error_message = f"Grype results file not found for repository {repo.repo_name}. Expected at: {grype_file_path}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # Read and parse Grype results from disk
    logger.info(f"Reading Grype results from disk for repo_id: {repo.repo_id}.")
    try:
        processed_vulnerabilities = parse_and_save_grype_results(grype_file_path, repo.repo_id, session)
    except Exception as e:
        error_message = f"Error while parsing or saving Grype results for repository {repo.repo_name}: {e}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Return a comprehensive success message
    return (
        f"{processed_vulnerabilities} vulnerabilities processed"
    )

def parse_and_save_grype_results(grype_file_path, repo_id, session):
    """
    Read Grype results from a file, parse them, and save to the database.

    :param grype_file_path: Path to the Grype analysis output file.
    :param repo_id: Repository ID being analyzed.
    :param session: Database session for saving results.
    :return: Number of vulnerabilities processed.
    """
    try:
        logger.info(f"Reading Grype results from: {grype_file_path}")
        with open(grype_file_path, "r") as file:
            grype_data = json.load(file)

        matches = grype_data.get("matches", [])
        if not matches:
            logger.info(f"No vulnerabilities found for repo_id: {repo_id}")
            return 0

        logger.debug(f"Found {len(matches)} vulnerabilities for repo_id: {repo_id}.")

        processed_vulnerabilities = 0
        for match in matches:
            vulnerability = match.get("vulnerability", {})
            artifact = match.get("artifact", {})
            locations = artifact.get("locations", [{}])

            cve = vulnerability.get("id", "No CVE")
            description = vulnerability.get("description", "No description provided")
            severity = vulnerability.get("severity", "UNKNOWN")
            package = artifact.get("name", "Unknown")
            version = artifact.get("version", "Unknown")
            file_path = locations[0].get("path", "N/A") if locations else "N/A"
            language = artifact.get("language", "Unknown")

            logger.debug(f"Saving vulnerability: {cve} for repo_id: {repo_id}, package: {package}.")

            session.execute(
                insert(GrypeResult).values(
                    repo_id=repo_id,
                    cve=cve,
                    description=description,
                    severity=severity,
                    package=package,
                    version=version,
                    file_path=file_path,
                    language=language
                ).on_conflict_do_update(
                    index_elements=["repo_id", "cve", "package", "version"],
                    set_={
                        "description": description,
                        "severity": severity,
                        "file_path": file_path,
                        "language": language
                    },
                )
            )
            processed_vulnerabilities += 1

        session.commit()
        logger.debug(f"Grype results successfully committed for repo_id: {repo_id}.")
        return processed_vulnerabilities

    except Exception as e:
        logger.exception(f"Error while parsing or saving Grype results for repository ID {repo_id}: {e}")
        raise

if __name__ == "__main__":
    # Hardcoded values for standalone execution
    repo_slug = "WebGoat"  # Changed from "halo" to "WebGoat"
    repo_id = "WebGoat"     # Changed from "halo" to "WebGoat"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = f"/tmp/{repo.repo_slug}"  # Changed to match "WebGoat"

    # Create a session and run Syft and Grype analysis
    session = Session()
    try:
        logger.info(f"Starting standalone Syft and Grype analysis for repo_id: {repo.repo_id}.")
        # Pass 'repo' as a keyword argument
        result = run_syft_and_grype_analysis(repo_dir, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone Syft and Grype analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone Syft and Grype analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}.")
