from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from modular.main.cloning import clone_repository, cleanup_repository_directory
from modular.main.metrics import calculate_and_persist_repo_metrics
from modular.main.language_analysis import perform_language_analysis
from modular.main.models import Session, Repository

# Analyze a single batch of repositories
def analyze_repositories(batch):
    session = Session()
    for repo in batch:
        try:
            # Clone repository
            repo_dir = clone_repository(repo)

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
        'repo_processing_with_batches',
        default_args=default_args,
        schedule_interval=None,
        max_active_tasks=10,
        catchup=False,
) as dag:

    # Fetch and divide repositories into batches
    batches = create_batches(batch_size=1000, num_tasks=10)

    # Create tasks for each batch
    for task_id, batch in enumerate(batches):
        PythonOperator(
            task_id=f"process_batch_{task_id}",
            python_callable=analyze_repositories,
            op_args=[batch],
        )
