import os
import subprocess
import json
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, GrypeResult
from modular.timer_decorator import log_time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SYFT_CONFIG_PATH = "/root/.syft/config.yaml"
GRYPE_CONFIG_PATH = "/root/.grype/config.yaml"

@log_time
def run_syft_and_grype_analysis(repo_dir, repo, session):
    """
    Run Syft to generate SBOM and Grype to analyze vulnerabilities, saving results to the database.
    """
    logger.info(f"Starting Syft and Grype analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    try:
        # Validate repository directory
        if not os.path.exists(repo_dir):
            logger.error(f"Repository directory does not exist: {repo_dir}")
            raise FileNotFoundError(f"Repository directory not found: {repo_dir}")

        logger.debug(f"Repository directory validated: {repo_dir}")

        # Generate SBOM using Syft
        sbom_file_path = os.path.join(repo_dir, "sbom.json")
        logger.info(f"Generating SBOM for repo_id: {repo.repo_id} using Syft.")
        try:
            subprocess.run(
                ["syft", repo_dir, "--output", "json", "--config", SYFT_CONFIG_PATH, "--file", sbom_file_path],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug(f"SBOM successfully generated at: {sbom_file_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Syft command failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
            raise RuntimeError("Syft analysis failed.") from e

        # Analyze SBOM using Grype and write results to disk
        grype_file_path = os.path.join(repo_dir, "grype-results.json")
        logger.info(f"Analyzing SBOM with Grype for repo_id: {repo.repo_id}.")
        try:
            subprocess.run(
                ["grype", f"sbom:{sbom_file_path}", "--config", GRYPE_CONFIG_PATH, "--output", "json", "--file", grype_file_path],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug(f"Grype results written to: {grype_file_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Grype command failed for repo_id {repo.repo_id}: {e.stderr.strip()}")
            raise RuntimeError("Grype analysis failed.") from e

        # Read and parse Grype results from disk
        logger.info(f"Reading Grype results from disk for repo_id: {repo.repo_id}.")
        parse_and_save_grype_results(grype_file_path, repo.repo_id, session)

    except Exception as e:
        logger.exception(f"Error during Syft and Grype analysis for repo_id {repo.repo_id}: {e}")
        raise


def parse_and_save_grype_results(grype_file_path, repo_id, session):
    """
    Read Grype results from a file, parse them, and save to the database.
    """
    try:
        # Read Grype results from the file
        logger.info(f"Reading Grype results from: {grype_file_path}")
        with open(grype_file_path, "r") as file:
            grype_data = json.load(file)

        matches = grype_data.get("matches", [])
        if not matches:
            logger.info(f"No vulnerabilities found for repo_id: {repo_id}")
            return

        logger.debug(f"Found {len(matches)} vulnerabilities for repo_id: {repo_id}.")

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
                ).on_conflict_do_update(
                    index_elements=["repo_id", "cve", "package", "version"],
                    set_={
                        "description": description,
                        "severity": severity,
                        "file_path": file_path,
                    },
                )
            )
        session.commit()
        logger.debug(f"Grype results successfully committed for repo_id: {repo_id}.")

    except Exception as e:
        logger.exception(f"Error saving Grype results for repo_id {repo_id}: {e}")
        raise


if __name__ == "__main__":
    from modular.models import Session

    # Hardcoded values for standalone execution
    repo_slug = "halo"
    repo_id = "halo"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id, repo_slug)
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create a session and run Syft and Grype analysis
    session = Session()
    try:
        logger.info(f"Starting standalone Syft and Grype analysis for repo_id: {repo.repo_id}.")
        run_syft_and_grype_analysis(repo_dir, repo, session)
        logger.info(f"Standalone Syft and Grype analysis completed successfully for repo_id: {repo.repo_id}.")
    except Exception as e:
        logger.error(f"Error during standalone Syft and Grype analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}.")
