import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from modular.cloning import clone_repository, cleanup_repository_directory
from modular.metrics import calculate_and_persist_repo_metrics
from modular.language_analysis import perform_language_analysis
from modular.lizard_analysis import run_lizard_analysis
from modular.cloc_analysis import run_cloc_analysis
from modular.models import Session, Repository

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Analyze a single batch of repositories
def analyze_repositories(batch):
    session = Session()
    for repo in batch:
        try:
            # Clone repository
            repo_dir = clone_repository(repo)

            run_lizard_analysis(repo_dir, repo, session)

            # Run Cloc analysis
            run_cloc_analysis(repo_dir, repo, session)

            # Perform language analysis
            perform_language_analysis(repo_dir, repo, session)

            # Calculate and persist metrics
            calculate_and_persist_repo_metrics(repo_dir, repo, session)

            # Update repository status to COMPLETED
            repo.status = "COMPLETED"
            repo.comment = "Processing completed successfully."
            repo.updated_on = datetime.utcnow()
            session.add(repo)
            session.commit()
        except Exception as e:
            # Update repository status to ERROR
            repo.status = "ERROR"
            repo.comment = str(e)
            repo.updated_on = datetime.utcnow()
            session.add(repo)
            session.commit()
        finally:
            # Cleanup repository directory
            cleanup_repository_directory(repo_dir)
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
default_args = {'owner': 'airflow', 'start_date': datetime(2023, 12, 1), 'retries': 1}

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
            op_args=[batch],
        )
