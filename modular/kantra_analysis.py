#!/usr/bin/env python3

import os
import subprocess
import logging

RULESET_PATHS = [
    "~/porfolios/tools/kantra/rulesets/build-tool/detect-maven-java.yaml",
    "~/tools/kantra/rulesets"
]

def find_pom_file(search_dir):
    pom_path = os.path.join(search_dir, "pom.xml")
    return pom_path if os.path.isfile(pom_path) else None

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
    search_dir = os.getcwd()
    pom_file = find_pom_file(search_dir)
    if not pom_file:
        logging.info("No pom.xml found in current directory. Exiting.")
        return
    logging.info(f"Found pom.xml at: {pom_file}")
    effective_pom_file = generate_effective_pom(search_dir)
    if not effective_pom_file:
        logging.info("Failed to generate effective POM. Exiting.")
        return
    logging.info(f"Effective POM generated at: {effective_pom_file}")
    output_dir = os.path.join(search_dir, "kantra-output")
    run_kantra_analysis(search_dir, output_dir, RULESET_PATHS)

if __name__ == "__main__":
    main()