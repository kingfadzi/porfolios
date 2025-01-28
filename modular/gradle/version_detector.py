import os
import re
import subprocess
from modular.base_logger import BaseLogger
import logging

class GradleVersionDetector(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger("GradleVersionDetector")
        self.logger.setLevel(logging.DEBUG)
        self.available_versions = {
            4: "4.10.3",
            5: "5.6.4",
            6: "6.9.4",
            7: "7.6.1",
            8: {"default": "8.8", "latest": "8.12"}
        }

    def detect_gradle_command(self, repo_dir):
        if self._is_executable(os.path.join(repo_dir, "gradlew")):
            return "./gradlew"

        if not self._is_gradle_project(repo_dir):
            self.logger.info(f"Directory '{repo_dir}' is not a Gradle project. No Gradle command will be run.")
            return None

        gradle_version = self.detect_version(repo_dir)
        if gradle_version:
            compatible_version = self._get_compatible_version(gradle_version)
            gradle_path = f"/opt/gradle/gradle-{compatible_version}/bin/gradle"
            if self._is_executable(gradle_path):
                return gradle_path

        self.logger.info(f"No compatible Gradle version or executable found for '{repo_dir}'.")
        return None

    def detect_version(self, repo_dir):
        if not self._is_gradle_project(repo_dir):
            return None

        return self._get_wrapper_version(repo_dir) or self._get_system_gradle_version()

    def _is_gradle_project(self, repo_dir):
        gradle_files = ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties"]
        return any(os.path.isfile(os.path.join(repo_dir, file)) for file in gradle_files) or \
            os.path.isdir(os.path.join(repo_dir, "gradle", "wrapper"))

    def _get_wrapper_version(self, repo_dir):
        path = os.path.join(repo_dir, "gradle", "wrapper", "gradle-wrapper.properties")
        return self._parse_version(path, r"distributionUrl=.*gradle-(\d+\.\d+).*")

    def _get_system_gradle_version(self):
        try:
            output = subprocess.run(["gradle", "-v"], capture_output=True, text=True, check=True).stdout
            return self._parse_version(output, r"Gradle\s+(\d+\.\d+).*", from_file=False)
        except FileNotFoundError:
            self.logger.error("System Gradle not found. Please install Gradle or ensure it is in your PATH.")
        except subprocess.CalledProcessError as ex:
            self.logger.error(f"System Gradle command failed: {ex}")
        return None

    def _get_compatible_version(self, version):
        major, minor = map(int, version.split(".")[:2])
        return (
            self.available_versions.get(major) if major < 8
            else self.available_versions[8]["latest"] if minor >= 12
            else self.available_versions[8]["default"]
        )

    def _parse_version(self, source, pattern, from_file=True):
        if from_file and not os.path.isfile(source):
            return None

        try:
            content = open(source).read() if from_file else source
            match = re.search(pattern, content)
            return match.group(1) if match else None
        except Exception as e:
            self.logger.error(f"Failed to parse version from {'file' if from_file else 'output'}: {e}")
            return None
        finally:
            if from_file:
                with open(source, "r") as f:
                    return f.read()

    def _is_executable(self, path):
        return os.path.isfile(path) and os.access(path, os.X_OK)
