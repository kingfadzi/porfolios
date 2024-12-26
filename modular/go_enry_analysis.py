import os
import subprocess
import logging
from datetime import datetime
from modular.models import import Session, LanguageAnalysis
from sqlalchemy.dialects.postgresql import insert
from modular.timer_decorator import log_time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@log_time
def run_enry_analysis(repo_dir, repo, session):
    """Perform language analysis using go-enry and persist results."""
    logger.info(f"Starting language analysis for repository: {repo.repo_name} (ID: {repo.repo_id})")
    analysis_file = f"{repo_dir}/analysis.txt"

    # Check if the repository directory exists
    if not os.path.exists(repo_dir):
        error_message = f"Repository directory does not exist: {repo_dir}"
        logger.error(error_message)
        # raise FileNotFoundError(error_message)
        return
    else:
        logger.debug(f"Repository directory found: {repo_dir}")

    # Run go-enry and generate the analysis file
    logger.info(f"Running go-enry in directory: {repo_dir}")
    try:
        subprocess.run(f"go-enry > {analysis_file}", shell=True, check=True, cwd=repo_dir)
        logger.info(f"Language analysis completed successfully. Output file: {analysis_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running go-enry for repository {repo.repo_name}: {e}")
        # raise RuntimeError(f"Language analysis failed for {repo.repo_name}: {e}")
        return

    # Validate the analysis file
    if not os.path.exists(analysis_file):
        error_message = f"Language analysis file not found for repository {repo.repo_name}. Expected at: {analysis_file}"
        logger.error(error_message)
        # raise FileNotFoundError(error_message)
        return

    # Parse and persist the language analysis results
    logger.info(f"Parsing language analysis results from file: {analysis_file}")
    try:
        with open(analysis_file, 'r') as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    percent_usage, language = parts
                    percent_usage = float(percent_usage.strip('%'))
                    logger.debug(f"Parsed result - Language: {language}, Usage: {percent_usage}%")

                    # Insert or update the analysis result in the database
                    session.execute(
                        insert(LanguageAnalysis).values(
                            repo_id=repo.repo_id,
                            language=language.strip(),
                            percent_usage=percent_usage
                        ).on_conflict_do_update(
                            index_elements=['repo_id', 'language'],
                            set_={'percent_usage': percent_usage, 'analysis_date': datetime.utcnow()}
                        )
                    )
        session.commit()
        logger.info(f"Language analysis results saved to the database for repo_id: {repo.repo_id}")
    except Exception as e:
        logger.error(f"Error while parsing or saving analysis results for repository {repo.repo_name}: {e}")
        # raise RuntimeError(f"Failed to persist language analysis for {repo.repo_name}: {e}")
        return

if __name__ == "__main__":
    # Hardcoded values for independent execution
    repo_slug = "example-repo"
    repo_id = "example-repo-id"

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug  # Mock additional attributes if needed

    repo = MockRepo(repo_id, repo_slug)

    # Define the path to the cloned repository
    repo_dir = f"/mnt/tmpfs/cloned_repositories/{repo.repo_slug}"

    # Create a session and run language analysis
    session = Session()
    try:
        logger.info(f"Running language analysis for hardcoded repo_id: {repo.repo_id}, repo_slug: {repo.repo_slug}")
        run_enry_analysis(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during standalone language analysis execution: {e}")
    finally:
        session.close()
        logger.info("Session closed.")
