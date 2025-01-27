import logging

from modular.base_logger import BaseLogger
from modular.config import Config

class JavaHomeSelector(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger("JavaHomeSelector")
        self.logger.setLevel(logging.DEBUG)

    def select_java_home(self, gradle_version):
        major, minor = self._parse_version(gradle_version)

        if major < 5:
            home = Config.JAVA_8_HOME
        elif major < 7:
            home = Config.JAVA_11_HOME
        elif major < 8:
            home = Config.JAVA_17_HOME
        elif major > 8:
            home = Config.JAVA_21_HOME
        else:
            home = self._select_for_gradle_8(minor)

        self.logger.info(f"For Gradle {gradle_version}, using JAVA_HOME={home}")
        return home

    def _select_for_gradle_8(self, minor):
        return Config.JAVA_21_HOME if minor >= 3 else Config.JAVA_17_HOME

    def _parse_version(self, v):
        parts = v.split('.')
        if len(parts) < 2:
            return (0, 0)
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return (0, 0)
