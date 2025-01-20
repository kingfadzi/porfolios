#!/usr/bin/env python3

import os
import subprocess
import logging

# Hardcoded repository directory
REPO_DIR = "~/tools/kantra/sonar-metrics"

# Hardcoded ruleset paths
RULESET_PATHS = [
    "~/porfolios/tools/kantra/rulesets/build-tool/detect-maven-java.yaml",
    "~/tools/kantra/rulesets"
]

def generate_effective_pom(project_dir, output_file="effective-pom.xml"):
    command = [
        "mvn",
        "help:effective-pom",
        f"-Doutput={output_file}"
    ]
    try:
        subprocess.run(command, cwd=project_dir, check=True)
        return os.path.join(project_dir, output_file)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error generating effective POM: {e}")
        return None

def run_kantra_analysis(input_dir, output_dir, ruleset_paths, overwrite=True):
    command = [
        "kantra",
        "analyze",
        f"--input={input_dir}",
        f"--output={output_dir}"
    ]
    for ruleset in ruleset_paths:
        command.append(f"--rules={os.path.expanduser(ruleset)}")
    if overwrite:
        command.append("--overwrite")

    try:
        subprocess.run(command, check=True)
        logging.info("Kantra analysis completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running Kantra analysis: {e}")

def main():
    logging.basicConfig(level=logging.INFO)

    # Expand and validate the hardcoded repository directory
    repo_dir = os.path.expanduser(REPO_DIR)
    if not os.path.isdir(repo_dir):
        logging.info(f"Repository directory does not exist: {repo_dir}. Exiting.")
        return

    logging.info(f"Using hardcoded repository directory: {repo_dir}")

    # Generate the effective POM
    effective_pom_file = generate_effective_pom(repo_dir)
    if not effective_pom_file:
        logging.info("Failed to generate effective POM. Exiting.")
        return

    logging.info(f"Effective POM generated at: {effective_pom_file}")

    # Run Kantra analysis
    output_dir = os.path.join(repo_dir, "kantra-output")
    run_kantra_analysis(repo_dir, output_dir, RULESET_PATHS)

if __name__ == "__main__":
    main()