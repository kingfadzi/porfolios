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
from modular.models import Session, Repository, AnalysisExecutionLog

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_repositories(batch, run_id, **kwargs):
    session = Session()
    for repo in batch:
        try:
            logger.info(f"Processing repository: {repo.repo_name} (ID: {repo.repo_id})")

            # Clone repository
            repo_dir = clone_repository(repo=repo, run_id=run_id)
            logger.debug(f"Repository cloned to: {repo_dir}")

            # Run analyses
            run_lizard_analysis(repo_dir=repo_dir, repo=repo, session=session, run_id=run_id)
            run_cloc_analysis(repo_dir=repo_dir, repo=repo, session=session, run_id=run_id)
            run_enry_analysis(repo_dir=repo_dir, repo=repo, session=session, run_id=run_id)
            run_gitlog_analysis(repo_dir=repo_dir, repo=repo, session=session, run_id=run_id)
            run_trivy_analysis(repo_dir=repo_dir, repo=repo, session=session, run_id=run_id)
            run_syft_and_grype_analysis(repo_dir=repo_dir, repo=repo, session=session, run_id=run_id)
            run_checkov_analysis(repo_dir=repo_dir, repo=repo, session=session, run_id=run_id)

        except Exception as e:
            logger.error(f"Error processing repository {repo.repo_name}: {e}")
            # Update repository status to ERROR
            repo.status = "ERROR"
            repo.comment = str(e)
            repo.updated_on = datetime.utcnow()
            session.add(repo)
            session.commit()
            logger.info(f"Repository {repo.repo_name} marked as ERROR.")
        finally:
            # Cleanup repository directory
            cleanup_repository_directory(repo_dir)
            logger.debug(f"Repository directory {repo_dir} cleaned up.")

        # Determine final status
        determine_final_status(repo, run_id, session)

    session.close()

def determine_final_status(repo, run_id, session):
    """
    Determine the final status of a repository after all analysis runs.

    :param repo: Repository object to update.
    :param run_id: The run ID for tracking.
    :param session: Database session.
    """
    logger.info(f"Determining final status for repository {repo.repo_name} (ID: {repo.repo_id}) with run_id: {run_id}")

    # Query all statuses related to the run_id
    analysis_statuses = (
        session.query(AnalysisExecutionLog.status)
        .filter(AnalysisExecutionLog.run_id == run_id, AnalysisExecutionLog.repo_id == repo.repo_id)
        .filter(AnalysisExecutionLog.status != "PROCESSING")
        .all()
    )

    if not analysis_statuses:
        # No records found for this run_id
        repo.status = "ERROR"
        repo.comment = "No analysis records found for this run ID."
    elif any(status == "FAILURE" for (status,) in analysis_statuses):
        # If any status is FAILED
        repo.status = "FAILURE"
        # repo.comment = "One or more analysis steps failed."
    elif all(status == "SUCCESS" for (status,) in analysis_statuses):
        # If all statuses are SUCCESS
        repo.status = "SUCCESS"
        repo.comment = "All analysis steps completed successfully."
    else:
        # Mixed statuses or other scenarios
        repo.status = "UNKNOWN"
        # repo.comment = "Couldnt figure out what happened during the analyses."

    # Update the repository object
    repo.updated_on = datetime.utcnow()
    session.add(repo)
    session.commit()
    logger.info(f"Final status for repository {repo.repo_name}: {repo.status} ({repo.comment})")


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
        max_active_tasks=5,
        catchup=False,
) as dag:

    # Fetch and divide repositories into batches
    batches = create_batches(batch_size=1000, num_tasks=5)

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
