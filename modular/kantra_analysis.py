import os
import subprocess
import logging
from modular.base_logger import BaseLogger
from modular.execution_decorator import analyze_execution
from modular.models import Session

class KantraAnalyzer(BaseLogger):
    OUTPUT_DIR = "~/tools/output"
    RULESET_PATHS = [
        "tools/kantra/rulesets/java-build-tool/detect-gradle-java.yaml",
        "tools/kantra/rulesets/java-build-tool/detect-maven-java.yaml",
        "tools/kantra/rulesets/spring-boot-gradle/spring-boot-nearing-eol-version.yaml",
        "tools/kantra/rulesets/spring-boot-gradle/spring-boot-supported-version.yaml",
        "tools/kantra/rulesets/spring-boot-gradle/spring-boot-unsupported-version.yaml",
        "tools/kantra/rulesets/spring-boot-maven/spring-boot-nearing-eol-version.yaml",
        "tools/kantra/rulesets/spring-boot-maven/spring-boot-supported-version.yaml",
        "tools/kantra/rulesets/spring-boot-maven/spring-boot-unsupported-version.yaml",
        "tools/kantra/rulesets/spring-framework-maven/spring-framework-nearing-eol-version.yaml",
        "tools/kantra/rulesets/spring-framework-maven/spring-framework-supported-version.yaml",
        "tools/kantra/rulesets/spring-framework-maven/spring-framework-unsupported-version.yaml",
        "tools/kantra/rulesets/spring-framework-gradle/spring-framework-nearing-eol-version.yaml",
        "tools/kantra/rulesets/spring-framework-gradle/spring-framework-supported-version.yaml",
        "tools/kantra/rulesets/spring-framework-gradle/spring-framework-unsupported-version.yaml",
    ]

    def __init__(self):
        self.logger = self.get_logger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    def check_java_version(self):
        try:
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True, check=True
            )
            self.logger.info(f"Java version:\n{result.stderr.strip()}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error checking Java version: {e}")
        except FileNotFoundError:
            self.logger.error("Java is not installed or not in PATH. Please install Java or set PATH correctly.")

    def generate_effective_pom(self, repo, output_file="effective-pom.xml"):
        try:
            pom_path = os.path.join(repo.directory, "pom.xml")
            if not os.path.exists(pom_path):
                self.logger.info("No pom.xml file found. Skipping effective POM generation.")
                return None
            command = ["mvn", "help:effective-pom", f"-Doutput={output_file}"]
            subprocess.run(command, cwd=repo.directory, capture_output=True, text=True, check=True)
            return os.path.join(repo.directory, output_file)
        except FileNotFoundError:
            self.logger.error("Maven is not installed or not in PATH. Please install Maven or set PATH correctly.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error generating effective POM: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during effective POM generation: {e}")

    @analyze_execution(session_factory=Session, stage="Kantra Analysis")
    def run_analysis(self, repo_dir, repo, session, run_id=None):
        self.logger.info(f"Starting Kantra analysis for repo_id: {repo.repo_id} (repo_slug: {repo.repo_slug}).")

        # Check if the directory exists
        if not os.path.exists(repo_dir):
            error_message = f"Repository directory does not exist: {repo_dir}"
            self.logger.error(error_message)
            raise FileNotFoundError(error_message)

        try:
            # Execute Kantra analysis
            ruleset_args = " ".join([f"--rules={os.path.abspath(path)}" for path in self.RULESET_PATHS])
            command = f"kantra analyze --input={repo_dir} --output={os.path.expanduser(self.OUTPUT_DIR)} {ruleset_args} --overwrite"
            self.logger.info(f"Executing Kantra command: {command}")
            subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            self.logger.info(f"Kantra analysis completed successfully for repo_id: {repo.repo_id}")
        except subprocess.CalledProcessError as e:
            error_message = f"Kantra command failed: {e.stderr.strip()}"
            self.logger.error(error_message)
            raise RuntimeError(error_message)
        except Exception as e:
            error_message = f"Unexpected error during Kantra analysis: {str(e)}"
            self.logger.error(error_message)
            raise


if __name__ == "__main__":
    repo_slug = "sonar-metrics"
    repo_id = "sonar-metrics"

    class MockRepo:
        def __init__(self, repo_id, repo_slug):
            self.repo_id = repo_id
            self.repo_slug = repo_slug
            self.repo_name = repo_slug
            self.directory = f"/Users/fadzi/tools/kantra/{repo_slug}"

    analyzer = KantraAnalyzer()
    repo = MockRepo(repo_id, repo_slug)

    # Attempt to initialize session
    try:
        session = Session()  # Ensure Session is properly imported and initialized
    except Exception as e:
        analyzer.logger.error(f"Failed to initialize database session: {e}")
        session = None

    try:
        analyzer.logger.info(f"Starting standalone Kantra analysis for repo_id: {repo.repo_id}.")
        if session is None:
            analyzer.logger.warning("Session is None. Skipping database-related operations.")
        result = analyzer.run_analysis(repo_dir=repo.directory, repo=repo, session=session, run_id="STANDALONE_RUN_001")
        analyzer.logger.info(f"Standalone Kantra analysis result: {result}")
    except Exception as e:
        analyzer.logger.error(f"Error during standalone Kantra analysis: {e}")
    finally:
        if session is not None:
            try:
                session.close()
                analyzer.logger.info(f"Database session closed for repo_id: {repo.repo_id}.")
            except Exception as e:
                analyzer.logger.error(f"Error closing session for repo_id: {repo.repo_id}: {e}")
        else:
            analyzer.logger.warning(f"No valid database session to close for repo_id: {repo.repo_id}.")
