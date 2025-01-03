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

            # Check for `self` and adjust `args` if necessary
            if len(args) > 0 and hasattr(args[0], "__class__"):  # Detect `self`
                args = args[1:]  # Skip `self`

            # Extract `repo` from kwargs or args
            repo = kwargs.get("repo") or (args[0] if args else None)

            decorator_logger.debug(f"Decorator received repo: {repo.__dict__ if hasattr(repo, '__dict__') else repo}")

            if not repo:
                session.close()
                raise ValueError(
                    f"Decorator for stage '{stage}' expected 'repo' but got None. "
                    f"Ensure you pass 'repo' either as the first positional argument or as a kwarg."
                )

            if not hasattr(repo, "repo_id"):
                session.close()
                raise ValueError(f"Expected attribute 'repo_id' missing in repo object: {repo}")

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

                decorator_logger.info(
                    f"Starting analysis {method_name} "
                    f"(Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id})..."
                )

                # Execute the actual function
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

                decorator_logger.info(
                    f"Analysis {method_name} (Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id}) "
                    f"completed successfully in {elapsed_time:.2f} seconds."
                )
                return result_message

            except Exception as e:
                elapsed_time = time.time() - start_time
                error_message = str(e)

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

                decorator_logger.error(
                    f"Analysis {method_name} (Stage: {stage}, Run ID: {run_id}, Repo ID: {repo_id}) "
                    f"failed in {elapsed_time:.2f} seconds: {error_message}"
                )
                raise RuntimeError(error_message)

            finally:
                session.close()
        return wrapper
    return decorator