import os
import subprocess
import logging

REPO_DIR = "~/tools/kantra/spring-boot-gradle"
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

def check_java_version():
    try:
        result = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, check=True
        )
        logging.info(f"Java version:\n{result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error checking Java version: {e}")
    except FileNotFoundError:
        logging.error("Java is not installed or not in PATH. Please install Java or set PATH correctly.")

def generate_effective_pom(project_dir, output_file="effective-pom.xml"):
    pom_path = os.path.join(project_dir, "pom.xml")
    if not os.path.exists(pom_path):
        logging.info("No pom.xml file found. Skipping effective POM generation.")
        return None
    command = ["mvn", "help:effective-pom", f"-Doutput={output_file}"]
    try:
        subprocess.run(command, cwd=project_dir, capture_output=True, text=True, check=True)
        return os.path.join(project_dir, output_file)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error generating effective POM: {e}")
        return None

def run_kantra_analysis(input_dir, output_dir, ruleset_paths):
    ruleset_args = " ".join([f"--rules={os.path.abspath(path)}" for path in ruleset_paths])
    command = f"kantra analyze --input={input_dir} --output={os.path.expanduser(output_dir)} {ruleset_args} --overwrite"
    try:
        subprocess.run(command, shell=True, check=True)
        logging.info("Kantra analysis completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running Kantra analysis: {e}")

def main():
    logging.basicConfig(level=logging.INFO)
    check_java_version()
    repo_dir = os.path.expanduser(REPO_DIR)
    if not os.path.isdir(repo_dir):
        logging.info(f"Repository directory does not exist: {repo_dir}. Exiting.")
        return
    generate_effective_pom(repo_dir)
    run_kantra_analysis(repo_dir, OUTPUT_DIR, RULESET_PATHS)

if __name__ == "__main__":
    main()
