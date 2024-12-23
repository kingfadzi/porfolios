import os
import subprocess
import logging
from datetime import datetime
from models import Session, Repository, LanguageAnalysis
from sqlalchemy.dialects.postgresql import insert

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def perform_language_analysis(repo_dir, repo, session):
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

if __name__ == "__main__":
    session = Session()
    repositories = session.query(Repository).filter_by(status="CLONED").limit(1).all()
    for repo in repositories:
        repo_dir = f"/mnt/tmpfs/cloned_repositories/{repo.repo_slug}"
        perform_language_analysis(repo_dir, repo, session)
    session.close()
