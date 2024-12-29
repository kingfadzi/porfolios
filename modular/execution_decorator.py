import time
import logging
import functools
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
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            session = session_factory()
            method_name = func.__name__
            run_id = kwargs.get("run_id", "N/A")  # Optional run_id from kwargs

            # Attempt to pull 'repo' from kwargs; if missing, fallback to args[0] if it exists
            repo = kwargs.get("repo") or (args[0] if args else None)

            if not repo:
                # If still None, fail early with a more direct error
                session.close()
                raise ValueError(
                    f"Decorator for stage '{stage}' expected 'repo' but got None. "
                    f"Ensure you pass 'repo' either as the first positional argument or as a kwarg."
                )

            repo_id = repo.repo_id  # Access repo_id directly from repo object
            start_time = time.time()

            try:
                session.add(AnalysisExecutionLog(
                    method_name=method_name,
                    stage=stage,
                    run_id=run_id,
                    repo_id=repo_id,
                    status="PROCESSING",
                    message=f"Starting analysis {method_name}",
                    execution_time=datetime.utcnow(),
                    duration=0
                ))
                session.commit()

                logger.info(
                    f"Starting analysis {method_name} "
                    f"(Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id})..."
                )
                result_message = func(*args, **kwargs)
                elapsed_time = time.time() - start_time

                # Log success to the database
                session.add(AnalysisExecutionLog(
                    method_name=method_name,
                    stage=stage,
                    run_id=run_id,
                    repo_id=repo_id,
                    status="SUCCESS",
                    message=result_message,
                    execution_time=datetime.utcnow(),
                    duration=elapsed_time
                ))
                session.commit()

                logger.info(
                    f"Analysis {method_name} (Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id}) "
                    "completed successfully."
                )
                return result_message

            except Exception as e:
                elapsed_time = time.time() - start_time
                error_message = str(e)

                repo.comment = error_message

                # Log failure to the database
                session.add(AnalysisExecutionLog(
                    method_name=method_name,
                    stage=stage,
                    run_id=run_id,
                    repo_id=repo_id,
                    status="FAILURE",
                    message=error_message,
                    execution_time=datetime.utcnow(),
                    duration=elapsed_time
                ))
                session.commit()

                logger.error(
                    f"Analysis {method_name} (Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id}) "
                    f"failed: {error_message}"
                )
                return error_message

            finally:
                session.close()
        return wrapper
    return decorator
