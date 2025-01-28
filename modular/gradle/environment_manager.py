import os
import re
import subprocess
from modular.base_logger import BaseLogger
from modular.config import Config
import logging

class GradleEnvironmentManager(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger("GradleEnvironmentManager")
        self.logger.setLevel(logging.DEBUG)
        self.available_gradle_versions = {
            4: "4.10.3",
            5: "5.6.4",
            6: "6.9.4",
            7: "7.6.1",
            8: {"default": "8.8", "latest": "8.12"}
        }

    def get_gradle_environment(self, repo_dir):
        self.logger.debug(f"Starting environment detection for directory: {repo_dir}")

        if not os.path.exists(repo_dir):
            self.logger.error(f"Directory '{repo_dir}' does not exist.")
            return None

        if not os.path.isdir(repo_dir):
            self.logger.error(f"Path '{repo_dir}' is not a directory.")
            return None

        if not self._is_gradle_project(repo_dir):
            self.logger.info(f"Directory '{repo_dir}' is not a Gradle project.")
            return None

        gradle_version = self._detect_gradle_version(repo_dir)
        if not gradle_version:
            self.logger.error("Unable to detect Gradle version.")
            return {
                "gradle_executable": None,
                "java_home": self._select_java_home(None)
            }

        java_home = self._select_java_home(gradle_version)
        gradle_executable = self._get_gradle_executable(repo_dir, gradle_version)

        if not gradle_executable:
            self.logger.warning("No suitable Gradle executable found. Assigning JAVA_HOME only.")
            return {
                "gradle_executable": None,
                "java_home": java_home
            }

        self.logger.info(f"Gradle environment detected: Executable={gradle_executable}, JAVA_HOME={java_home}")
        return {
            "gradle_executable": gradle_executable,
            "java_home": java_home
        }

    def _is_gradle_project(self, repo_dir):
        gradle_files = [
            "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties"
        ]

        has_gradle_files = any(os.path.isfile(os.path.join(repo_dir, file)) for file in gradle_files)
        has_wrapper_dir = os.path.isdir(os.path.join(repo_dir, "gradle", "wrapper"))

        is_project = has_gradle_files or has_wrapper_dir
        self.logger.debug(f"Checking if '{repo_dir}' is a Gradle project: {is_project} (Files: {has_gradle_files}, Wrapper: {has_wrapper_dir})")
        return is_project

    def _detect_gradle_version(self, repo_dir):
        wrapper_version = self._get_wrapper_version(repo_dir)
        if wrapper_version:
            self.logger.debug(f"Detected Gradle wrapper version: {wrapper_version}")
            return wrapper_version

        system_version = self._get_system_gradle_version()
        self.logger.debug(f"System Gradle version detected: {system_version}")
        return system_version

    def _get_wrapper_version(self, repo_dir):
        path = os.path.join(repo_dir, "gradle", "wrapper", "gradle-wrapper.properties")
        return self._parse_version_from_file(path, r"distributionUrl=.*gradle-(\d+\.\d+).*")

    def _get_system_gradle_version(self):
        try:
            output = subprocess.run(["gradle", "-v"], capture_output=True, text=True, check=True).stdout
            version = self._parse_version_from_output(output, r"Gradle\s+(\d+\.\d+\.\d+|\d+\.\d+)")
            return version
        except FileNotFoundError:
            self.logger.warning("System Gradle not found.")
        except subprocess.CalledProcessError as ex:
            self.logger.error(f"Error detecting system Gradle version: {ex}")
        return None

    def _select_java_home(self, gradle_version):
        if not gradle_version:
            self.logger.debug("Gradle version not detected; defaulting to JAVA_HOME for unknown versions.")
            return Config.JAVA_21_HOME

        major, minor = self._parse_version(gradle_version)
        if major < 5:
            return Config.JAVA_8_HOME
        if major < 7:
            return Config.JAVA_11_HOME
        if major < 8:
            return Config.JAVA_17_HOME
        if major == 8:
            return Config.JAVA_21_HOME if minor >= 3 else Config.JAVA_17_HOME
        return Config.JAVA_21_HOME

    def _get_gradle_executable(self, repo_dir, gradle_version):
        wrapper_path = os.path.join(repo_dir, "gradlew")
        if self._is_executable(wrapper_path):
            self.logger.debug(f"Using Gradle wrapper executable: {wrapper_path}")
            return wrapper_path

        gradle_path = self._get_compatible_gradle_path(gradle_version)
        if self._is_executable(gradle_path):
            self.logger.debug(f"Using Gradle executable from /opt: {gradle_path}")
            return gradle_path

        if self._is_executable("gradle"):
            self.logger.info("Using system Gradle as fallback.")
            return "gradle"

        self.logger.warning("No suitable Gradle executable found.")
        return None

    def _get_compatible_gradle_path(self, gradle_version):
        major, minor, *_ = map(int, gradle_version.split(".")[:3])
        compatible_version = self.available_gradle_versions.get(major)
        if isinstance(compatible_version, dict):
            return f"/opt/gradle/gradle-{compatible_version['latest' if minor >= 12 else 'default']}/bin/gradle"
        return f"/opt/gradle/gradle-{compatible_version}/bin/gradle" if compatible_version else None

    def _parse_version_from_file(self, path, pattern):
        if not os.path.isfile(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                match = re.search(pattern, content)
                return match.group(1) if match else None
        except Exception as ex:
            self.logger.error(f"Error reading version from {path}: {ex}")
        return None

    def _parse_version_from_output(self, output, pattern):
        match = re.search(pattern, output)
        return match.group(1) if match else None

    def _parse_version(self, version):
        parts = version.split(".")
        if len(parts) < 2:
            return (0, 0)
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return (0, 0)

    def _is_executable(self, path):
        return os.path.isfile(path) and os.access(path, os.X_OK)

if __name__ == "__main__":
    manager = GradleEnvironmentManager()
    env = manager.get_gradle_environment("/Users/fadzi/tools/gradle_projects/VyAPI")
    if env:
        print(f"Gradle Executable: {env['gradle_executable']}")
        print(f"JAVA_HOME: {env['java_home']}")
    else:
        print("No valid Gradle environment detected.")
