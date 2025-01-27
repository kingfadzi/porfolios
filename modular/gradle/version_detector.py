import os
import re
import logging
import subprocess

from modular.base_logger import BaseLogger

class GradleVersionDetector(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger("GradleVersionDetector")
        self.logger.setLevel(logging.DEBUG)

    def detect_version(self, repo_dir):
        wrapper_path = os.path.join(repo_dir, "gradlew")
        if os.path.isfile(wrapper_path) and os.access(wrapper_path, os.X_OK):
            props_file = os.path.join(repo_dir, "gradle", "wrapper", "gradle-wrapper.properties")
            version = self._parse_wrapper_properties(props_file)
            if version:
                self.logger.info(f"Detected Gradle version {version} from wrapper.")
                return version
            self.logger.debug("No valid version in gradle-wrapper.properties.")
        system_version = self._detect_system_gradle_version()
        if not system_version:
            self.logger.error("No Gradle wrapper or system Gradle found.")
            raise RuntimeError("Could not detect a valid Gradle version.")
        self.logger.info(f"Detected system Gradle version {system_version}.")
        return system_version

    def detect_gradle_command(self, repo_dir):
        wrapper_path = os.path.join(repo_dir, "gradlew")
        if os.path.isfile(wrapper_path) and os.access(wrapper_path, os.X_OK):
            self.logger.debug("Using ./gradlew.")
            return "./gradlew"
        self.logger.debug("No wrapper found. Using 'gradle'.")
        return "gradle"

    def _parse_wrapper_properties(self, path):
        if not os.path.isfile(path):
            return None
        pattern = re.compile(r'distributionUrl=.*gradle-(\d+\.\d+(\.\d+)?)\-')
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    return match.group(1)
        return None

    def _detect_system_gradle_version(self):
        try:
            result = subprocess.run(
                ["gradle", "-v"],
                capture_output=True,
                text=True,
                check=True
            )
            pattern = re.compile(r"Gradle\s+(\d+\.\d+(\.\d+)?)")
            for line in result.stdout.splitlines():
                match = pattern.search(line.strip())
                if match:
                    return match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError) as ex:
            self.logger.debug(f"System Gradle detection failed: {ex}")
        return None
