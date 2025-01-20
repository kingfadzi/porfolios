import os
import subprocess
import logging

RULESET_DIR = "/path/to/rulesets"
RULESET_FILE = "ruleset.rulest"

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

def run_kantra_analysis(input_dir, output_dir, ruleset_path, overwrite=True):
    command = [
        "kantra",
        "analyze",
        f"--input={input_dir}",
        f"--output={output_dir}",
        f"--rules={ruleset_path}"
    ]
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
    ruleset_path = os.path.join(RULESET_DIR, RULESET_FILE)
    if not os.path.isfile(ruleset_path):
        logging.info(f"No ruleset file found at: {ruleset_path}. Exiting.")
        return
    logging.info(f"Using ruleset file: {ruleset_path}")
    output_dir = os.path.join(search_dir, "kantra-output")
    run_kantra_analysis(search_dir, output_dir, ruleset_path)

if __name__ == "__main__":
    main()