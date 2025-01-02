import os
import json
import logging
import subprocess
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from modular.models import GoEnryAnalysis, SemgrepResult, Session
from modular.execution_decorator import analyze_execution  # Added import
from modular.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve SEMGREP_RULESET from Config class
SEMGREP_RULESET = Config.SEMGREP_RULESET

class SemgrepAnalyzer:
    def __init__(self):
        # Create a class-specific logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set the desired log level for this class

        # Create a handler (e.g., StreamHandler for console output)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

@analyze_execution(session_factory=Session, stage="Semgrep Analysis")
def run_semgrep_analysis(repo, repo_dir, session, run_id=None):
    """
    Run Semgrep analysis dynamically based on the languages detected in the repository.

    :param repo: Repository object containing repo_id and other metadata.
    :param repo_dir: Directory path of the repository to be scanned.
    :param session: Database session to query and persist results.
    :param run_id: DAG run ID passed for tracking.
    :return: Success message for logging or raises an exception for errors.
    """
    logger.info(f"Starting Semgrep analysis for repo_id: {repo.repo_id}")

    try:
        # 1) Query languages for the repository
        languages = get_languages_from_db(repo.repo_id, session)
        if not languages:
            message = f"No languages detected for repo_id: {repo.repo_id}. Skipping Semgrep scan."
            logger.warning(message)
            return message

        # 2) Construct the Semgrep command
        semgrep_command = construct_semgrep_command(repo_dir, languages)
        if not semgrep_command:
            message = f"No valid Semgrep rulesets found for repo_id: {repo.repo_id}. Skipping Semgrep scan."
            logger.warning(message)
            return message

        # 3) Execute Semgrep
        logger.info(f"Executing Semgrep command: {' '.join(semgrep_command)}")
        result = subprocess.run(semgrep_command, capture_output=True, text=True, check=True)
        semgrep_data = json.loads(result.stdout.strip())

        # 4) Save results to the database
        findings_count = save_semgrep_results(session, repo.repo_id, semgrep_data)

        message = f"Semgrep analysis completed for repo_id: {repo.repo_id} with {findings_count} findings."
        logger.info(message)
        return message

    except subprocess.CalledProcessError as e:
        error_message = f"Semgrep command failed for repo_id: {repo.repo_id}. Error: {e.stderr.strip()}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    except json.JSONDecodeError as e:
        error_message = f"Failed to parse Semgrep output for repo_id: {repo.repo_id}. Error: {str(e)}"
        logger.error(error_message)
        raise ValueError(error_message)

    except Exception as e:
        error_message = f"Unexpected error during Semgrep analysis for repo_id: {repo.repo_id}. Error: {str(e)}"
        logger.error(error_message)
        raise RuntimeError(error_message)


def get_languages_from_db(repo_id, session):
    """
    Query the `GoEnryAnalysis` table to retrieve all languages for a given repo_id.

    :param repo_id: Repository ID.
    :param session: Database session.
    :return: List of languages for the repository.
    """
    logger.info(f"Querying languages for repo_id: {repo_id}")
    stmt = select(GoEnryAnalysis.language).where(GoEnryAnalysis.repo_id == repo_id)
    result = session.execute(stmt).fetchall()
    if result:
        return [row.language for row in result]  # Extract the 'language' column from each row
    return []


def construct_semgrep_command(repo_dir, languages):
    """
    Construct the Semgrep CLI command based on the languages.

    :param repo_dir: Directory of the repository.
    :param languages: List of languages detected in the repository.
    :return: Semgrep CLI command as a list or None if no valid rulesets are found.
    """
    if not SEMGREP_RULESET:
        logger.error("SEMGREP_RULESET environment variable is not set.")
        return None

    rulesets = []
    for lang in languages:
        lang_lower = lang.lower()
        ruleset_path = os.path.join(SEMGREP_RULESET, lang_lower)
        if os.path.exists(ruleset_path):
            rulesets.append(ruleset_path)
            logger.info(f"Found Semgrep ruleset for language '{lang}': {ruleset_path}")
        else:
            logger.warning(f"Semgrep ruleset for language '{lang}' does not exist at path: {ruleset_path}. Skipping.")

    if not rulesets:
        logger.warning(f"No valid Semgrep rulesets found for the detected languages: {languages}. Skipping Semgrep scan.")
        return None

    # Construct the Semgrep command
    command = ["semgrep", "--experimental", "--json", "--skip-unknown", repo_dir, "--verbose"]
    for ruleset in rulesets:
        command.extend(["--config", ruleset])

    return command


def save_semgrep_results(session, repo_id, semgrep_data):
    """
    Save Semgrep findings to the database using upsert logic to avoid duplicates.

    :param session: Database session.
    :param repo_id: Repository ID being analyzed.
    :param semgrep_data: Parsed Semgrep JSON results.
    :return: Number of findings saved or updated.
    """
    logger.info(f"Saving Semgrep findings for repo_id: {repo_id}")
    total_upserts = 0

    for result in semgrep_data.get("results", []):
        # Extract metadata from the result
        metadata = result["extra"].get("metadata", {})

        # Normalize fields
        technology = ", ".join(metadata.get("technology", []))  # Convert list to comma-separated string
        cwe = ", ".join(metadata.get("cwe", []))  # Convert list to comma-separated string
        subcategory = ", ".join(metadata.get("subcategory", []))  # Convert list to comma-separated string
        likelihood = metadata.get("likelihood", "")
        impact = metadata.get("impact", "")
        confidence = metadata.get("confidence", "")
        category = metadata.get("category", "")

        finding = {
            "repo_id": repo_id,
            "path": result.get("path"),
            "start_line": result["start"]["line"],
            "end_line": result["end"]["line"],
            "rule_id": result.get("check_id"),
            "severity": result["extra"].get("severity"),
            "message": result["extra"].get("message"),
            "category": category,
            "subcategory": subcategory,
            "technology": technology,
            "cwe": cwe,
            "likelihood": likelihood,
            "impact": impact,
            "confidence": confidence,
        }

        try:
            # Use PostgreSQL upsert
            stmt = insert(SemgrepResult).values(**finding)
            stmt = stmt.on_conflict_do_update(
                index_elements=["repo_id", "path", "start_line", "rule_id"],  # Unique constraint
                set_={
                    "end_line": stmt.excluded.end_line,
                    "severity": stmt.excluded.severity,
                    "message": stmt.excluded.message,
                    "category": stmt.excluded.category,
                    "subcategory": stmt.excluded.subcategory,
                    "technology": stmt.excluded.technology,
                    "cwe": stmt.excluded.cwe,
                    "likelihood": stmt.excluded.likelihood,
                    "impact": stmt.excluded.impact,
                    "confidence": stmt.excluded.confidence,
                }
            )
            session.execute(stmt)
            total_upserts += 1
        except Exception as e:
            logger.error(f"Failed to upsert Semgrep finding: {finding}. Error: {e}")
            raise RuntimeError(f"Failed to upsert findings: {e}")

    session.commit()
    logger.info(f"Upserted {total_upserts} findings for repo_id: {repo_id}")
    return total_upserts


if __name__ == "__main__":
    # Configure logging for standalone run
    # logging.basicConfig(level=logging.DEBUG)
    # logger = logging.getLogger(__name__)

    # Hardcoded values for a standalone test
    repo_slug = "WebGoat"
    repo_id = "WebGoat"  # Changed ID for clarity

    # Mock repo object
    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug

    repo = MockRepo(repo_id=repo_id, repo_slug=repo_slug)
    repo_dir = f"/tmp/{repo.repo_slug}"

    # Create a session and run Semgrep analysis
    session = Session()
    try:
        logger.info(f"Starting standalone Semgrep analysis for mock repo_id: {repo.repo_id}")
        # Pass the MockRepo object
        result = run_semgrep_analysis(repo, repo_dir, session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone Semgrep analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone Semgrep analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")
