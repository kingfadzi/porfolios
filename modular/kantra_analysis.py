import os
import yaml
import subprocess
import logging
from sqlalchemy.dialects.postgresql import insert

from modular.base_logger import BaseLogger
from modular.execution_decorator import analyze_execution
from modular.models import Session, Ruleset, Violation, Label
from modular.config import Config


class KantraAnalyzer(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    @analyze_execution(session_factory=Session, stage="Kantra Analysis")
    def run_analysis(self, repo_dir, repo, session, run_id=None):
        self.logger.info(f"Starting Kantra analysis for repo_id: {repo.repo_id} ({repo.repo_slug}).")

        if not os.path.exists(repo_dir):
            raise FileNotFoundError(f"Repository directory does not exist: {repo_dir}")
        if not os.path.exists(Config.KANTRA_RULESET_FILE):
            raise FileNotFoundError(f"Ruleset file not found: {Config.KANTRA_RULESET_FILE}")

        effective_pom_path = self.generate_effective_pom(repo_dir)
        if effective_pom_path:
            self.logger.info(f"Generated effective POM at: {effective_pom_path}")

        output_dir = os.path.join(Config.KANTRA_OUTPUT_ROOT, f"kantra_output_{repo.repo_slug}")
        os.makedirs(output_dir, exist_ok=True)

        command = self.build_kantra_command(repo_dir, output_dir)
        self.logger.info(f"Executing Kantra command: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=600,
                text=True,
                check=True
            )
            self.logger.info(f"Kantra analysis completed for repo_id: {repo.repo_id}")

            output_yaml_path = os.path.join(output_dir, "output.yaml")
            analysis_data = self.parse_output_yaml(output_yaml_path)
            self.save_kantra_results(session, repo.repo_id, analysis_data)
            self.logger.info(f"Kantra results persisted for repo_id: {repo.repo_id}")

        except subprocess.CalledProcessError as e:
            err_msg = f"Kantra command failed with exit code {e.returncode}"
            if e.stdout:
                self.logger.error(f"Stdout:\n{e.stdout.strip()}")
            if e.stderr:
                self.logger.error(f"Stderr:\n{e.stderr.strip()}")
            self.logger.error(err_msg)
            raise RuntimeError(f"Kantra command failed: {e.stderr.strip()}")

        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Kantra command timed out: {e}")
            raise

        except Exception as e:
            error_message = f"Unexpected error during Kantra analysis: {e}"
            self.logger.error(error_message)
            raise

    def build_kantra_command(self, repo_dir, output_dir):
        return (
            f"kantra analyze "
            f"--input={repo_dir} "
            f"--output={output_dir} "
            f"--rules={os.path.abspath(Config.KANTRA_RULESET_FILE)} "
            f"--enable-default-rulesets=false "            
            f"--overwrite"
        )

    def generate_effective_pom(self, repo_dir, output_file="effective-pom.xml"):
        try:
            pom_path = os.path.join(repo_dir, "pom.xml")
            if not os.path.exists(pom_path):
                self.logger.info("No pom.xml found. Skipping effective POM generation.")
                return None

            command = ["mvn", "help:effective-pom", f"-Doutput={output_file}"]
            subprocess.run(command, cwd=repo_dir, capture_output=True, text=True, check=True)
            return os.path.join(repo_dir, output_file)

        except Exception as e:
            self.logger.error(f"Unexpected error during effective POM generation: {e}")

    def parse_output_yaml(self, yaml_file):
        if not os.path.isfile(yaml_file):
            self.logger.warning(f"Output YAML file not found: {yaml_file}")
            return None
        try:
            with open(yaml_file, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error reading/parsing YAML file {yaml_file}: {e}")
            return None

    def save_kantra_results(self, session, repo_id, analysis_data):
        self.logger.debug(f"Processing Kantra results for repo_id: {repo_id}")
        if not analysis_data:
            self.logger.warning("No data found to persist. Skipping database updates.")
            return

        try:
            for ruleset_data in analysis_data:
                ruleset_name = ruleset_data.get("name")
                description = ruleset_data.get("description")

                session.execute(
                    insert(Ruleset)
                    .values(name=ruleset_name, description=description)
                    .on_conflict_do_update(
                        index_elements=["name"],
                        set_={"description": description}
                    )
                )

                for _, violation_data in ruleset_data.get("violations", {}).items():
                    if not violation_data or not violation_data.get("description"):
                        continue

                    violation_desc = violation_data["description"]
                    category = violation_data.get("category")
                    effort = violation_data.get("effort")

                    session.execute(
                        insert(Violation)
                        .values(
                            repo_id=repo_id,
                            ruleset_name=ruleset_name,
                            description=violation_desc,
                            category=category,
                            effort=effort
                        )
                        .on_conflict_do_update(
                            index_elements=["repo_id", "ruleset_name", "description"],
                            set_={"category": category, "effort": effort}
                        )
                    )

                    labels = violation_data.get("labels", [])
                    for label_str in labels:
                        if "=" in label_str:
                            key, value = label_str.split("=", 1)
                            session.execute(
                                insert(Label)
                                .values(key=key, value=value)
                                .on_conflict_do_nothing(
                                    index_elements=["key", "value"]
                                )
                            )
                        else:
                            self.logger.warning(f"Skipping invalid label format: {label_str}")

            session.commit()
            self.logger.debug(f"Kantra results committed for repo_id: {repo_id}")

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving Kantra results for repo_id {repo_id}: {e}")
            raise

    def check_java_version(self):
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, text=True, check=True)
            self.logger.info(f"Java version:\n{result.stderr.strip()}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error checking Java version: {e}")
        except FileNotFoundError:
            self.logger.error("Java is not installed or not in PATH.")
