import subprocess
import json
import csv
import os
import sys

def run_semgrep(target_directory, ruleset, output_json):
    """
    Runs Semgrep on the target directory and saves results as a JSON file.
    """
    try:
        # Run Semgrep command
        command = [
            "semgrep",
            "--config", ruleset,
            target_directory,
            "--json",
            "--output", output_json
        ]
        print(f"Running Semgrep: {' '.join(command)}")
        subprocess.run(command, check=True)
        print(f"Semgrep results saved to {output_json}")
    except subprocess.CalledProcessError as e:
        print(f"Error running Semgrep: {e}")
        sys.exit(1)

def convert_json_to_csv(json_file, csv_file):
    """
    Converts Semgrep JSON results to a CSV file.
    """
    try:
        # Load the JSON file
        with open(json_file, "r") as f:
            semgrep_data = json.load(f)

        # Open the CSV file for writing
        with open(csv_file, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)

            # Write the header row
            header = ["Path", "Start Line", "End Line", "Rule ID", "Message", "Severity"]
            csvwriter.writerow(header)

            # Write the data rows
            for result in semgrep_data.get("results", []):
                row = [
                    result.get("path", ""),
                    result.get("start", {}).get("line", ""),
                    result.get("end", {}).get("line", ""),
                    result.get("check_id", ""),
                    result.get("extra", {}).get("message", ""),
                    result.get("extra", {}).get("severity", ""),
                ]
                csvwriter.writerow(row)

        print(f"CSV results saved to {csv_file}")
    except Exception as e:
        print(f"Error converting JSON to CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Directory to scan
    target_directory = "/path/to/codebase"  # Replace with your directory

    # Semgrep ruleset (local or registry-based)
    ruleset = "./cloned-rules/python/security"  # Replace with your ruleset path

    # Output file paths
    output_json = "semgrep_results.json"
    output_csv = "semgrep_results.csv"

    # Run Semgrep and process results
    run_semgrep(target_directory, ruleset, output_json)
    convert_json_to_csv(output_json, output_csv)
