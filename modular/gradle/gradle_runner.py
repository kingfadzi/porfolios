import os
import logging
import subprocess

from modular.base_logger import BaseLogger
from modular.config import Config
from modular.gradle.java_home_selector import JavaHomeSelector

class GradleRunner(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger("GradleRunner")
        self.logger.setLevel(logging.DEBUG)
        self.java_selector = JavaHomeSelector()  # We'll instantiate it here

    def run(self, cmd, cwd, gradle_version, check=True):
        java_home = self.java_selector.select_java_home(gradle_version)
        env = self._setup_env(java_home)
        self.logger.info(f"Running Gradle command: {' '.join(cmd)} in {cwd}")
        try:
            result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=check)
            self.logger.debug(f"Return code: {result.returncode}")
            if result.stdout:
                self.logger.debug(f"Stdout:\n{result.stdout}")
            if result.stderr:
                self.logger.debug(f"Stderr:\n{result.stderr}")
            return result
        except subprocess.CalledProcessError as cpe:
            self.logger.error(f"Gradle command failed with CalledProcessError: {cpe}")
            return None
        except Exception as ex:
            self.logger.error(f"Unexpected error: {ex}")
            return None

    def _setup_env(self, java_home):
        env = os.environ.copy()
        env["JAVA_HOME"] = java_home
        env["GRADLE_OPTS"] = self._build_gradle_opts(env.get("GRADLE_OPTS", ""))
        return env

    def _build_gradle_opts(self, existing_opts):
        opts = [existing_opts] if existing_opts else []
        if getattr(Config, "HTTP_PROXY_HOST", None) and getattr(Config, "HTTP_PROXY_PORT", None):
            opts.append(f"-Dhttp.proxyHost={Config.HTTP_PROXY_HOST}")
            opts.append(f"-Dhttp.proxyPort={Config.HTTP_PROXY_PORT}")
        if getattr(Config, "HTTPS_PROXY_HOST", None) and getattr(Config, "HTTPS_PROXY_PORT", None):
            opts.append(f"-Dhttps.proxyHost={Config.HTTPS_PROXY_HOST}")
            opts.append(f"-Dhttps.proxyPort={Config.HTTPS_PROXY_PORT}")
        if getattr(Config, "TRUSTSTORE_PATH", None):
            opts.append(f"-Djavax.net.ssl.trustStore={Config.TRUSTSTORE_PATH}")
        if getattr(Config, "TRUSTSTORE_PASSWORD", None):
            opts.append(f"-Djavax.net.ssl.trustStorePassword={Config.TRUSTSTORE_PASSWORD}")
        return " ".join(opts).strip()
