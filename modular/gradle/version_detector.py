import os
import re
import subprocess

from modular.base_logger import BaseLogger

class GradleVersionDetector(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger("GradleVersionDetector")
        self.logger.setLevel(logging.DEBUG)

    def detect_version(self, repo_dir):
        if not self._is_gradle_project(repo_dir):
            self.logger.info(f"Directory '{repo_dir}' does not appear to be a Gradle project.")
            return None

        version = self._detect_wrapper_version(repo_dir) or self._detect_system_gradle_version(fallback=True)
        if version:
            self.logger.info(f"Detected Gradle version {version}.")
            return version

        raise RuntimeError("No Gradle wrapper or system Gradle installation found.")

    def detect_gradle_command(self, repo_dir):
        wrapper_path = os.path.join(repo_dir, "gradlew")
        if os.path.isfile(wrapper_path) and os.access(wrapper_path, os.X_OK):
            self.logger.debug("Using ./gradlew.")
            return "./gradlew"
        self.logger.debug("No wrapper found. Using 'gradle'.")
        return "gradle"

    def _is_gradle_project(self, repo_dir):
        indicators = [
            os.path.isfile(os.path.join(repo_dir, "gradlew")),
            any(os.path.isfile(os.path.join(repo_dir, file))
                for file in ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"]),
            os.path.isfile(os.path.join(repo_dir, "gradle.properties")),
            os.path.isdir(os.path.join(repo_dir, "gradle", "wrapper"))
        ]
        return any(indicators)

    def _detect_wrapper_version(self, repo_dir):
        wrapper_properties = os.path.join(repo_dir, "gradle", "wrapper", "gradle-wrapper.properties")
        version = self._parse_wrapper_properties(wrapper_properties)
        if version:
            self.logger.info(f"Detected Gradle version {version} from wrapper.")
        return version

    def _parse_wrapper_properties(self, path):
        if not os.path.isfile(path):
            return None
        pattern = re.compile(r'distributionUrl=.*gradle-(\d+\.\d+(\.\d+)?)\-')
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if match := pattern.search(line):
                    return match.group(1)
        return None

    def _detect_system_gradle_version(self, fallback=False):
        try:
            result = subprocess.run(
                ["gradle", "-v"],
                capture_output=True,
                text=True,
                check=True
            )
            pattern = re.compile(r"Gradle\s+(\d+\.\d+(\.\d+)?)")
            for line in result.stdout.splitlines():
                if match := pattern.search(line.strip()):
                    return match.group(1)
        except FileNotFoundError:
            self.logger.error("System Gradle not found. Please install Gradle or ensure it is in your PATH.")
            if fallback:
                raise RuntimeError("Gradle wrapper missing and no system Gradle found.")
        except subprocess.CalledProcessError as ex:
            self.logger.error(f"System Gradle command failed: {ex}")
        return None
