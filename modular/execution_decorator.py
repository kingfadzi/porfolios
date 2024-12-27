import time
import logging
from datetime import datetime
from modular.models import AnalysisExecutionLog

logger = logging.getLogger(__name__)

def analyze_execution(session_factory, stage=None):
    """
    Decorator to track and log analysis execution details (status, duration, etc.) to the database.

    :param session_factory: Callable that provides a database session (e.g., Session).
    :param stage: Optional stage name for the function (e.g., "Trivy Analysis").
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            session = session_factory()
            method_name = func.__name__
            run_id = kwargs.get("run_id", "N/A")  # Optional run_id from kwargs

            # Extract repo_id from the "repo" argument
            repo = kwargs.get("repo")  # Assumes "repo" is always passed in
            repo_id = repo.repo_id  # Access repo_id directly from repo object

            start_time = time.time()

            try:
                logger.info(f"Starting analysis {method_name} (Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id})...")
                result_message = func(*args, **kwargs)
                elapsed_time = time.time() - start_time

                # Log success to the database
                session.add(AnalysisExecutionLog(
                    method_name=method_name,
                    stage=stage,
                    run_id=run_id,
                    repo_id=repo_id,  # Include repo_id
                    status="SUCCESS",
                    message=result_message,
                    execution_time=datetime.utcnow(),
                    duration=elapsed_time
                ))
                session.commit()

                logger.info(f"Analysis {method_name} (Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id}) completed successfully.")
                return result_message

            except Exception as e:
                elapsed_time = time.time() - start_time
                error_message = str(e)

                # Log failure to the database
                session.add(AnalysisExecutionLog(
                    method_name=method_name,
                    stage=stage,
                    run_id=run_id,
                    repo_id=repo_id,  # Include repo_id
                    status="FAILURE",
                    message=error_message,
                    execution_time=datetime.utcnow(),
                    duration=elapsed_time
                ))
                session.commit()

                logger.error(f"Analysis {method_name} (Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id}) failed: {error_message}")
                return error_message

            finally:
                session.close()
        return wrapper
    return decorator
