import time
import logging
import functools
from datetime import datetime
from modular.models import AnalysisExecutionLog

# Configure logging
logging.basicConfig(level=logging.DEBUG)
decorator_logger = logging.getLogger("AnalyzeExecutionDecorator")
decorator_logger.setLevel(logging.DEBUG)  # Log at DEBUG level for the decorator

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

            # Attempt to pull 'repo' from kwargs; fallback to args[0] if it exists
            repo = kwargs.get("repo") or (args[0] if args else None)

            if not repo:
                decorator_logger.error(
                    f"Decorator for stage '{stage}' expected 'repo' but got None. "
                    f"Ensure you pass 'repo' either as the first positional argument or as a kwarg."
                )
                session.close()
                raise ValueError(f"Missing 'repo' for stage '{stage}' in {method_name}")

            repo_id = repo.repo_id  # Access repo_id directly from repo object
            start_time = time.time()

            try:
                # Log the start of analysis
                decorator_logger.debug(
                    f"Initializing analysis for method: {method_name}, "
                    f"stage: {stage}, run_id: {run_id}, repo_id: {repo_id}."
                )
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

                result_message = func(*args, **kwargs)
                elapsed_time = time.time() - start_time

                # Log success
                decorator_logger.debug(
                    f"Completed analysis for method: {method_name}, "
                    f"stage: {stage}, run_id: {run_id}, repo_id: {repo_id}. "
                    f"Duration: {elapsed_time:.2f}s"
                )
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

                return result_message

            except Exception as e:
                elapsed_time = time.time() - start_time
                error_message = str(e)

                # Log the error
                decorator_logger.error(
                    f"Error during analysis for method: {method_name}, "
                    f"stage: {stage}, run_id: {run_id}, repo_id: {repo_id}. "
                    f"Duration: {elapsed_time:.2f}s. Error: {error_message}"
                )
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

                return error_message

            finally:
                decorator_logger.debug(
                    f"Finalizing session for method: {method_name}, "
                    f"stage: {stage}, run_id: {run_id}, repo_id: {repo_id}."
                )
                session.close()
        return wrapper
    return decorator