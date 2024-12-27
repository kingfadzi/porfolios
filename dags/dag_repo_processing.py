import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from modular.cloning import clone_repository, cleanup_repository_directory
from modular.gitlog_analysis import run_gitlog_analysis
from modular.go_enry_analysis import run_enry_analysis
from modular.lizard_analysis import run_lizard_analysis
from modular.cloc_analysis import run_cloc_analysis
from modular.syft_grype_analysis import run_syft_and_grype_analysis
from modular.trivy_analysis import run_trivy_analysis
from modular.checkov_analysis import run_checkov_analysis
from modular.models import Session, Repository

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_repositories(batch, run_id, **kwargs):
    """
    Analyze a batch of repositories by running various analysis tools.

    :param batch: List of Repository objects to analyze.
    :param run_id: The DAG run ID for tracking.
    :param kwargs: Additional keyword arguments from Airflow.
    """
    session = Session()
    for repo in batch:
        try:
            logger.info(f"Processing repository: {repo.repo_name} (ID: {repo.repo_id})")

            # Clone repository
            repo_dir = clone_repository(repo)
            logger.debug(f"Repository cloned to: {repo_dir}")

            # Run Lizard Analysis
            run_lizard_analysis(repo_dir, repo, session, run_id=run_id)

            # Run Cloc Analysis
            run_cloc_analysis(repo_dir, repo, session, run_id=run_id)

            # Perform Language Analysis with go-enry
            run_enry_analysis(repo_dir, repo, session, run_id=run_id)

            # Calculate and Persist GitLog Metrics
            run_gitlog_analysis(repo_dir, repo, session, run_id=run_id)

            # Run Dependency-Check Analysis
            run_trivy_analysis(repo_dir, repo, session, run_id=run_id)

            # Run Syft and Grype Analysis
            run_syft_and_grype_analysis(repo_dir, repo, session, run_id=run_id)

            # Run Checkov Analysis
            run_checkov_analysis(repo_dir, repo, session, run_id=run_id)

            # Update repository status to COMPLETED
            repo.status = "COMPLETED"
            repo.comment = "Processing completed successfully."
            repo.updated_on = datetime.now(timezone.utc)
            session.add(repo)
            session.commit()
            logger.info(f"Repository {repo.repo_name} processed successfully.")

        except Exception as e:
            logger.error(f"Error processing repository {repo.repo_name}: {e}")
            # Update repository status to ERROR
            repo.status = "ERROR"
            repo.comment = str(e)
            repo.updated_on = datetime.now(timezone.utc)
            session.add(repo)
            session.commit()
            logger.info(f"Repository {repo.repo_name} marked as ERROR.")
        finally:
            # Cleanup repository directory
            cleanup_repository_directory(repo_dir)
            logger.debug(f"Repository directory {repo_dir} cleaned up.")
    session.close()

# Fetch repositories in batches
def fetch_repositories(batch_size=1000):
    session = Session()
    offset = 0
    while True:
        batch = session.query(Repository).filter_by(status="NEW").offset(offset).limit(batch_size).all()
        if not batch:
            break
        yield batch
        offset += batch_size
    session.close()

# Create repository batches for DAG tasks
def create_batches(batch_size=1000, num_tasks=10):
    logger.info("Fetching repositories and creating batches.")
    all_repositories = [repo for batch in fetch_repositories(batch_size) for repo in batch]
    task_batches = [all_repositories[i::num_tasks] for i in range(num_tasks)]
    logger.info(f"Created {len(task_batches)} batches for processing.")
    return task_batches

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 12, 1),
    'retries': 1
}

# Define DAG
with DAG(
        'modular_processing_with_batches',
        default_args=default_args,
        schedule_interval=None,
        max_active_tasks=1,
        catchup=False,
) as dag:

    # Fetch and divide repositories into batches
    batches = create_batches(batch_size=1000, num_tasks=1)

    # Create tasks for each batch
    for task_id, batch in enumerate(batches):
        PythonOperator(
            task_id=f"process_batch_{task_id}",
            python_callable=analyze_repositories,
            op_kwargs={
                'batch': batch,
                'run_id': '{{ run_id }}'  # Pass run_id using Jinja templating
            },
        )
