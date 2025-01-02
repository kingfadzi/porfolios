import os
import json
import logging
import subprocess
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from modular.models import SemgrepResult, Session  # Updated model name
from modular.execution_decorator import analyze_execution


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Path to the mapping file
RULESET_MAPPING_FILE = os.path.expanduser("~/semgrep/language_ruleset_map.txt")


@analyze_execution(session_factory=Session, stage="Semgrep Analysis")
def run_semgrep_analysis(repo_id, repo_dir, session, run_id=None):
    """
    Run Semgrep analysis dynamically based on the languages detected in the repository.

    :param repo_id: Repository ID.
    :param repo_dir: Directory path of the repository to be scanned.
    :param session: Database session to query and persist results.
    :param run_id: DAG run ID passed for tracking.
    :return: Success message for logging or raises an exception for errors.
    """
    logger.info(f"Starting Semgrep analysis for repo_id: {repo_id}")

    try:
        # 1) Query languages for the repository
        languages = get_languages_from_db(repo_id, session)
        if not languages:
            message = f"No languages detected for repo_id: {repo_id}. Skipping Semgrep scan."
            logger.warning(message)
            return message

        # 2) Construct the Semgrep command
        semgrep_command = construct_semgrep_command(repo_dir, languages)
        if not semgrep_command:
            message = f"No valid Semgrep rulesets found for repo_id: {repo_id}. Skipping Semgrep scan."
            logger.warning(message)
            return message

        # 3) Execute Semgrep
        logger.info(f"Executing Semgrep command: {' '.join(semgrep_command)}")
        result = subprocess.run(semgrep_command, capture_output=True, text=True, check=True)
        semgrep_data = json.loads(result.stdout.strip())

        # 4) Save results to the database
        findings_count = save_semgrep_results(session, repo_id, semgrep_data)

        message = f"Semgrep analysis completed for repo_id: {repo_id} with {findings_count} findings."
        logger.info(message)
        return message

    except subprocess.CalledProcessError as e:
        error_message = f"Semgrep command failed for repo_id: {repo_id}. Error: {e.stderr.strip()}"
        logger.error(error_message)
        raise RuntimeError(error_message)

    except json.JSONDecodeError as e:
        error_message = f"Failed to parse Semgrep output for repo_id: {repo_id}. Error: {str(e)}"
        logger.error(error_message)
        raise ValueError(error_message)

    except Exception as e:
        error_message = f"Unexpected error during Semgrep analysis for repo_id: {repo_id}. Error: {str(e)}"
        logger.error(error_message)
        raise RuntimeError(error_message)


def load_language_ruleset_map():
    """
    Load the language-to-ruleset mapping from a text file.

    :return: A dictionary with language-to-ruleset mappings.
    """
    mapping = {}
    try:
        with open(RULESET_MAPPING_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line and "=" in line:  # Skip empty lines or invalid lines
                    language, ruleset = line.split("=", 1)
                    mapping[language.strip()] = ruleset.strip()
        logger.info(f"Loaded language-to-ruleset mapping from {RULESET_MAPPING_FILE}")
        return mapping
    except FileNotFoundError:
        logger.error(f"Ruleset mapping file not found: {RULESET_MAPPING_FILE}")
        raise
    except Exception as e:
        logger.error(f"Failed to load ruleset mapping file: {e}")
        raise


def get_languages_from_db(repo_id, session):
    """
    Query the `go_enry_analysis` table to retrieve all languages for a given repo_id.

    :param repo_id: Repository ID.
    :param session: Database session.
    :return: List of languages for the repository.
    """
    logger.info(f"Querying languages for repo_id: {repo_id}")
    stmt = select(go_enry_analysis.c.language).where(go_enry_analysis.c.repo_id == repo_id)
    result = session.execute(stmt).fetchall()
    if result:
        return [row.language for row in result]  # Extract the 'language' column from each row
    return []


def construct_semgrep_command(repo_dir, languages):
    """
    Construct the Semgrep CLI command based on the languages.

    :param repo_dir: Directory of the repository.
    :param languages: List of languages detected in the repository.
    :return: Semgrep CLI command as a list or None if no mapped rulesets are found.
    """
    # Load the dynamic mapping
    language_ruleset_map = load_language_ruleset_map()

    rulesets = [
        language_ruleset_map[lang]
        for lang in languages
        if lang in language_ruleset_map
    ]

    if not rulesets:
        logger.warning(f"No mapped rulesets found for the detected languages: {languages}. Skipping Semgrep scan.")
        return None

    # Add the --experimental flag to the command
    command = ["semgrep", "--experimental", "--json", repo_dir]
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
        finding = {
            "repo_id": repo_id,
            "path": result.get("path"),
            "start_line": result["start"]["line"],
            "end_line": result["end"]["line"],
            "rule_id": result.get("check_id"),
            "severity": result["extra"].get("severity"),
            "message": result["extra"].get("message"),
        }

        try:
            # Use PostgreSQL upsert
            stmt = insert(SemgrepResult).values(**finding)  # Updated model name
            stmt = stmt.on_conflict_do_update(
                index_elements=["repo_id", "path", "start_line", "rule_id"],  # Unique constraint
                set_={
                    "end_line": stmt.excluded.end_line,
                    "severity": stmt.excluded.severity,
                    "message": stmt.excluded.message,
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
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

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
        # Pass the MockRepo object instead of repo.repo_id
        result = run_semgrep_analysis(repo, repo_dir, session, run_id="STANDALONE_RUN_001")
        logger.info(f"Standalone Semgrep analysis result: {result}")
    except Exception as e:
        logger.error(f"Error during standalone Semgrep analysis: {e}")
    finally:
        session.close()
        logger.info(f"Database session closed for repo_id: {repo.repo_id}")

