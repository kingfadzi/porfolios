from git import Repo, GitCommandError, InvalidGitRepositoryError
from datetime import datetime, timezone
import os
import subprocess
import logging
from sqlalchemy.dialects.postgresql import insert
from modular.models import Session, GoEnryAnalysis
from modular.execution_decorator import analyze_execution

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@analyze_execution(session_factory=Session, stage="Go Enry Analysis")
def run_enry_analysis(repo_dir, repo, session, run_id=None):
    """Perform language analysis using go-enry and persist results."""
    logger.info(f"Starting language analysis for repository: {repo.repo_name} (ID: {repo.repo_id})")
    analysis_file = os.path.join(repo_dir, "analysis.txt")

    # Check if the repository directory exists
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)
    else:
        logger.debug(f"Repository directory found: {repo_dir}")

    # Run go-enry and generate the analysis file
    logger.info(f"Running go-enry in directory: {repo_dir}")
    try:
        # Ensure the analysis file is writable
        with open(analysis_file, "w") as outfile:
            subprocess.run(
                ["go-enry"],
                stdout=outfile,
                stderr=subprocess.PIPE,
                check=True,
                cwd=repo_dir
            )
        logger.info(f"Language analysis completed successfully. Output file: {analysis_file}")
    except subprocess.CalledProcessError as e:
        error_message = f"Error running go-enry for repository {repo.repo_name}: {e.stderr.decode().strip()}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Validate the analysis file
    if not os.path.exists(analysis_file):
        error_message = f"Language analysis file not found for repository {repo.repo_name}. Expected at: {analysis_file}"
        logger.error(error_message)
        raise FileNotFoundError(error_message)

    # Parse and persist the language analysis results
    logger.info(f"Parsing language analysis results from file: {analysis_file}")
    try:
        processed_languages = parse_and_persist_enry_results(repo.repo_id, analysis_file, session)
    except Exception as e:
        error_message = f"Error while parsing or saving analysis results for repository {repo.repo_name}: {e}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Return a comprehensive success message without the "Metrics saved for" prefix
    return (
        f"{processed_languages} languages processed"
    )


def parse_and_persist_enry_results(repo_id, analysis_file_path, session):
    """
    Parse the go-enry analysis output and persist the results to the database.

    :param repo_id: Repository ID being analyzed.
    :param analysis_file_path: Path to the go-enry analysis output file.
    :param session: Database session for saving results.
    :return: Number of languages processed.
    """
    try:
        logger.info(f"Reading analysis file at: {analysis_file_path}")
        with open(analysis_file_path, "r") as f:
            processed_languages = 0
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    percent_usage, language = parts
                    try:
                        percent_usage = float(percent_usage.strip('%'))
                    except ValueError:
                        logger.warning(f"Invalid percentage format for language '{language}': {percent_usage}")
                        continue

                    logger.debug(f"Parsed result - Language: {language}, Usage: {percent_usage}%")

                    # Insert or update the analysis result in the database
                    session.execute(
                        insert(GoEnryAnalysis).values(
                            repo_id=repo_id,
                            language=language.strip(),
                            percent_usage=percent_usage,
                            analysis_date=datetime.now(timezone.utc)  # Timezone-aware datetime
                        ).on_conflict_do_update(
                            index_elements=['repo_id', 'language'],
                            set_={
                                'percent_usage': percent_usage,
                                'analysis_date': datetime.now(timezone.utc)
                            }
                        )
                    )
                    processed_languages += 1
        session.commit()
        logger.info(f"Language analysis results saved to the database for repo_id: {repo_id}")
        return processed_languages
    except Exception as e:
        logger.exception(f"Error while parsing or saving analysis results for repository ID {repo_id}: {e}")
        raise


if __name__ == "__main__":
    # Hardcoded values for standalone execution
    repo_slug = "WebGoat"
    repo_id = "WebGoat"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)

    # Define the path to the cloned repository
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create a session and run language analysis
    session = Session()
    try:
        logger.info(f"Running language analysis for hardcoded repo_id: {repo.repo_id}, repo_slug: {repo.repo_slug}")
        result = run_enry_analysis(repo_dir, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone language analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone language analysis execution: {e}")
    finally:
        session.close()
        logger.info("Session closed.")
