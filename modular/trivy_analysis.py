import os
import json
import logging
import subprocess
import shutil
from sqlalchemy.dialects.postgresql import insert
from modular.execution_decorator import analyze_execution
from modular.models import Session, TrivyVulnerability
from modular.config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Path to the central .trivyignore file
TRIVYIGNORE_TEMPLATE = Config.TRIVYIGNORE_TEMPLATE

@analyze_execution(session_factory=Session, stage="Trivy Analysis")
def run_trivy_analysis(repo_dir, repo, session, run_id=None):
    """
    Run Trivy analysis on the given repo_dir and persist vulnerabilities to the database.

    :param repo_dir: Directory path of the repository to be scanned.
    :param repo: Repository object containing metadata like repo_id and repo_slug.
    :param session: Database session to persist the results.
    :param run_id: DAG run ID passed for tracking.
    :return: Success message with the number of vulnerabilities or raises an exception on failure.
    """
    logger.info(f"Starting Trivy analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

    # 1) Validate repository directory
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # 2) Execute the Trivy command to scan the directory
    logger.info(f"Executing Trivy command in directory: {repo_dir}")
    try:

        prepare_trivyignore(repo_dir)

        result = subprocess.run(
            ["trivy", "fs", "--skip-db-update", "--skip-java-db-update", "--offline-scan", "--format", "json", repo_dir],
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"Trivy command completed successfully for repo_id: {repo.repo_id}")
    except subprocess.CalledProcessError as e:
        error_message = (f"Trivy command failed for repo_id {repo.repo_id}. "
                         f"Return code: {e.returncode}. Error: {e.stderr.strip()}")
        logger.error(error_message)
        raise RuntimeError(error_message)

    # 3) Parse the Trivy output
    stdout_str = result.stdout.strip()
    if not stdout_str:
        error_message = f"No output from Trivy command for repo_id: {repo.repo_id}"
        logger.error(error_message)
        raise ValueError(error_message)

    logger.info(f"Parsing Trivy output for repo_id: {repo.repo_id}")
    try:
        trivy_data = json.loads(stdout_str)
    except json.JSONDecodeError as e:
        error_message = f"Error decoding Trivy JSON output: {str(e)}"
        logger.error(error_message)
        raise ValueError(error_message)

    # 4) Persist results to the database
    logger.info(f"Saving Trivy vulnerabilities to the database for repo_id: {repo.repo_id}")
    try:
        total_vulnerabilities = save_trivy_results(session, repo.repo_id, trivy_data)
    except Exception as e:
        error_message = f"Error saving Trivy vulnerabilities: {str(e)}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Return a formatted success message
    return f"{total_vulnerabilities} vulnerabilities found."

def prepare_trivyignore(repo_dir):
    """Copy the .trivyignore file to the repository directory if it doesn't already exist."""
    trivyignore_path = os.path.join(repo_dir, ".trivyignore")
    try:
        if not os.path.exists(trivyignore_path):
            logger.info(f"Copying .trivyignore to {repo_dir}")
            shutil.copy(TRIVYIGNORE_TEMPLATE, trivyignore_path)

            # Print the content of the TRIVYIGNORE_TEMPLATE
            with open(TRIVYIGNORE_TEMPLATE, 'r') as template_file:
                content = template_file.read()
                print("Trivy Template Content:")
                print(content)
        else:
            logger.info(f".trivyignore already exists in {repo_dir}")
    except FileNotFoundError:
        logger.error(f"Trivy template file not found: {TRIVYIGNORE_TEMPLATE}")
    except PermissionError:
        logger.error(f"Permission denied when accessing {TRIVYIGNORE_TEMPLATE} or {trivyignore_path}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


def save_trivy_results(session, repo_id, results):
    """
    Save Trivy vulnerabilities to the database in the TrivyVulnerability table.

    :param session: Database session.
    :param repo_id: Repository ID being analyzed.
    :param results: Parsed Trivy JSON results.
    :return: Number of vulnerabilities saved.
    :raises: RuntimeError if saving to the database fails.
    """
    logger.debug(f"Processing Trivy vulnerabilities for repo_id: {repo_id}")

    try:
        total_vulnerabilities = 0  # Track the number of vulnerabilities saved

        for item in results.get("Results", []):
            target = item.get("Target")
            vulnerabilities = item.get("Vulnerabilities", [])

            resource_class = item.get("Class", None)
            resource_type = item.get("Type", None)

            for vuln in vulnerabilities:
                total_vulnerabilities += 1  # Increment the count for each vulnerability
                session.execute(
                    insert(TrivyVulnerability).values(
                        repo_id=repo_id,
                        target=target,
                        resource_class=resource_class,
                        resource_type=resource_type,
                        vulnerability_id=vuln.get("VulnerabilityID"),
                        pkg_name=vuln.get("PkgName"),
                        installed_version=vuln.get("InstalledVersion"),
                        fixed_version=vuln.get("FixedVersion"),
                        severity=vuln.get("Severity"),
                        primary_url=vuln.get("PrimaryURL"),
                        description=vuln.get("Description"),
                    ).on_conflict_do_update(
                        index_elements=["repo_id", "vulnerability_id", "pkg_name"],
                        set_={
                            "resource_class": resource_class,
                            "resource_type": resource_type,
                            "installed_version": vuln.get("InstalledVersion"),
                            "fixed_version": vuln.get("FixedVersion"),
                            "severity": vuln.get("Severity"),
                            "primary_url": vuln.get("PrimaryURL"),
                            "description": vuln.get("Description"),
                        }
                    )
                )

        session.commit()
        logger.debug(f"Trivy vulnerabilities committed to the database for repo_id: {repo_id}")
        return total_vulnerabilities  # Return the total number of vulnerabilities

    except Exception as e:
        error_message = f"Error saving Trivy vulnerabilities for repo_id {repo_id}: {e}"
        logger.exception(error_message)
        raise RuntimeError(error_message)


if __name__ == "__main__":
    # Configure logging for standalone run
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Hardcoded values for a standalone test
    repo_slug = "WebGoat"
    repo_id = "WebGoat"  # Changed ID for clarity

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id=repo_id, repo_slug=repo_slug)
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create a session and run Trivy analysis
    session = Session()
    try:
        logger.info(f"Starting standalone Trivy analysis for mock repo_id: {repo.repo_id}")
        # Ensure repo is passed as a keyword argument
        result = run_trivy_analysis(repo_dir, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone Trivy analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone Trivy analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
