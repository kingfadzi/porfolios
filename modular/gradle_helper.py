import os
import re
import logging
import subprocess
import uuid
from modular.base_logger import BaseLogger
from modular.config import Config

GRADLE_TASK_SNIPPET = r"""
task {TASK_NAME} {
    outputs.upToDateWhen { false }
    doLast {
        def outputFile = new File("${rootProject.buildDir}/reports/all-deps-nodupes.txt")
        outputFile.parentFile.mkdirs()
        def visited = new HashSet<String>()

        def visitDependencyTree = { dep ->
            def id = "${dep.moduleGroup}:${dep.moduleName}:${dep.moduleVersion}"
            if (visited.add(id)) {
                dep.children.each { visitDependencyTree(it) }
            }
        }

        project.allprojects { proj ->
            proj.configurations.each { cfg ->
                try {
                    cfg.resolvedConfiguration.lenientConfiguration.allModuleDependencies.each { dep ->
                        visitDependencyTree(dep)
                    }
                } catch (Exception e) {
                    logger.warn("Error resolving ${cfg.name} in ${proj.name}: ${e.message}")
                }
            }
        }

        outputFile.text = visited.join("\n")
        logger.lifecycle("Dependencies written to: ${outputFile.absolutePath}")
        logger.lifecycle("Total unique dependencies: ${visited.size()}")
    }
}
"""

class GradleHelper(BaseLogger):
    def __init__(self):
        self.logger = self.get_logger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    def generate_resolved_dependencies(self, repo_dir, output_file="all-deps-nodupes.txt"):
        self.logger.info(f"Generating resolved dependencies for repo: {repo_dir}")
        if not os.path.isdir(repo_dir):
            self.logger.error(f"Repository directory does not exist or is not a directory: {repo_dir}")
            return None

        build_file = self._find_build_file(repo_dir)
        if not build_file:
            self.logger.warning("No Gradle build file found (build.gradle or build.gradle.kts).")
            return None

        unique_task_name = f"allDependenciesNoDupes_{uuid.uuid4().hex[:8]}"
        snippet = GRADLE_TASK_SNIPPET.replace("{TASK_NAME}", unique_task_name)
        self._inject_snippet(build_file, snippet)

        gradle_cmd = self._detect_gradle_command(repo_dir)
        self.logger.info(f"Using Gradle command: {gradle_cmd}")

        success = self._run_gradle_task(repo_dir, [gradle_cmd, unique_task_name])
        if not success:
            self.logger.info("Custom task failed. Attempting fallback 'dependencies' command.")
            return self._fallback_dependencies(repo_dir, gradle_cmd, output_file)

        final_path = self._get_output_path(repo_dir, output_file)
        if final_path:
            self.logger.info(f"Gradle dependencies written to: {final_path}")
        else:
            self.logger.debug("No dependencies file found after running the custom task.")
        return final_path

    def _find_build_file(self, repo_dir):
        self.logger.debug(f"Looking for build.gradle or build.gradle.kts in: {repo_dir}")
        for filename in ["build.gradle", "build.gradle.kts"]:
            path = os.path.join(repo_dir, filename)
            if os.path.isfile(path):
                self.logger.debug(f"Found Gradle build file: {path}")
                return path
        return None

    def _inject_snippet(self, build_file, snippet):
        self.logger.debug(f"Injecting Gradle snippet into: {build_file}")
        try:
            with open(build_file, "a", encoding="utf-8") as f:
                f.write(f"\n{snippet}\n")
            self.logger.debug(f"Snippet injected successfully.")
        except Exception as e:
            self.logger.error(f"Failed injecting snippet into {build_file}: {e}")

    def _detect_gradle_command(self, repo_dir):
        wrapper_path = os.path.join(repo_dir, "gradlew")
        if os.path.isfile(wrapper_path) and os.access(wrapper_path, os.X_OK):
            self.logger.debug("Detected gradlew wrapper script.")
            return "./gradlew"
        self.logger.debug("No gradlew wrapper; defaulting to system 'gradle' command.")
        return "gradle"

    def _run_gradle_task(self, repo_dir, cmd):
        self.logger.info(f"Running Gradle task with command: {cmd}")
        result = self._run_command(cmd, repo_dir, check=True)
        return result and (result.returncode == 0)

    def _fallback_dependencies(self, repo_dir, gradle_cmd, output_file):
        self.logger.debug("Running fallback: gradle dependencies --configuration implementation.")
        result = self._run_command(
            [gradle_cmd, "dependencies", "--configuration", "implementation", "--console=plain"],
            repo_dir,
            check=False
        )
        if not result or result.returncode != 0:
            self.logger.error("Fallback 'dependencies' command also failed.")
            return None

        fallback_path = os.path.join(repo_dir, output_file)
        self.logger.debug(f"Writing fallback output to: {fallback_path}")
        try:
            with open(fallback_path, "w", encoding="utf-8") as f:
                f.write(result.stdout)
            self.logger.info(f"Fallback dependencies written to: {fallback_path}")
        except Exception as e:
            self.logger.error(f"Error writing fallback output: {e}")
            return None
        return fallback_path

    def _get_output_path(self, repo_dir, output_file):
        paths = [
            os.path.join(repo_dir, "build", "reports", output_file),
            os.path.join(repo_dir, output_file)
        ]
        for p in paths:
            if os.path.isfile(p):
                return p
        return None

    def _run_command(self, cmd, cwd, check=True):
        java_home = self._select_java_home_for_gradle(cwd)
        if not java_home:
            self.logger.error("No suitable JAVA_HOME found. Aborting command.")
            return None

        env = os.environ.copy()
        env["JAVA_HOME"] = java_home
        self.logger.info(f"Forcing JAVA_HOME to: {java_home}")
        self.logger.debug(f"Executing command: {' '.join(cmd)} in {cwd}")

        try:
            result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=check)
            self.logger.debug(f"Command return code: {result.returncode}")
            if result.stdout:
                self.logger.debug(f"Command stdout:\n{result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"Command stderr:\n{result.stderr.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with CalledProcessError: {e}\nStdout:\n{e.stdout}\nStderr:\n{e.stderr}")
        except Exception as ex:
            self.logger.error(f"Unexpected error running {cmd}: {ex}")
        return None

    def _select_java_home_for_gradle(self, repo_dir):
        wrapper_props = os.path.join(repo_dir, "gradle", "wrapper", "gradle-wrapper.properties")
        if not os.path.isfile(wrapper_props):
            self.logger.warning("No gradle-wrapper.properties found; defaulting to Java 17.")
            return Config.JAVA_17_HOME

        version = self._parse_gradle_version(wrapper_props)
        if not version:
            self.logger.warning("Could not parse Gradle version; defaulting to Java 17.")
            return Config.JAVA_17_HOME

        major, minor = version
        if major < 5:
            chosen = Config.JAVA_8_HOME
        elif major < 7:
            chosen = Config.JAVA_11_HOME
        else:
            chosen = Config.JAVA_17_HOME

        self.logger.info(f"Detected Gradle {major}.{minor}, using {chosen}")
        return chosen

    def _parse_gradle_version(self, props_path):
        pattern = re.compile(r'distributionUrl=.*gradle-(\d+)\.(\d+)')
        self.logger.debug(f"Parsing Gradle version from {props_path}")
        with open(props_path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    maj, min = int(match.group(1)), int(match.group(2))
                    self.logger.debug(f"Parsed Gradle version: {maj}.{min}")
                    return maj, min
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    helper = GradleHelper()
    repo = "/Users/fadzi/tools/sonar-metrics"
    deps_file = helper.generate_resolved_dependencies(repo)
    if deps_file:
        print(f"Dependencies file: {deps_file}")
    else:
        print("Failed to generate dependencies.")
