import os
import subprocess
import logging
from datetime import datetime
from models import Session, LanguageAnalysis
from sqlalchemy.dialects.postgresql import insert

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def perform_language_analysis(repo_dir, repo, session):
    """Perform language analysis using go-enry and persist results."""
    analysis_file = f"{repo_dir}/analysis.txt"

    try:
        subprocess.run(f"go-enry > {analysis_file}", shell=True, check=True, cwd=repo_dir)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Language analysis failed: {e}")

    if not os.path.exists(analysis_file):
        raise FileNotFoundError("Language analysis file not found.")

    with open(analysis_file, 'r') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                percent_usage, language = parts
                percent_usage = float(percent_usage.strip('%'))
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
    logger.info(f"Language analysis completed for repo_id: {repo.repo_id}.")

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
        logger.info(f"Running language analysis for repo_id: {repo.repo_id}, repo_slug: {repo.repo_slug}")
        perform_language_analysis(repo_dir, repo, session)
    except Exception as e:
        logger.error(f"Error during language analysis: {e}")
    finally:
        session.close()
