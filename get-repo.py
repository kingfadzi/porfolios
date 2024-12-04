import csv
import gitlab
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse, quote

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Replace these with your GitLab instance details
GITLAB_URL = "https://gitlab.example.com"  # GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token
INPUT_FILE = "input_projects.csv"          # Input CSV file with project details
OUTPUT_FILE = "output_project_metrics.csv" # Output CSV file with metrics

# Initialize the GitLab client with SSL verification disabled
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

# Function to get project ID from URL
def get_project_id_from_url(project_url):
    print(f"Original URL: {project_url}")
    try:
        parsed_url = urlparse(project_url)
        project_path = parsed_url.path.strip("/")  # Extract path
        print(f"Extracted project path: {project_path}")
        encoded_path = quote(project_path, safe="")  # Encode path for API
        print(f"Encoded path for API: {encoded_path}")

        # Use the exact API endpoint
        print(f"Making API call to fetch project ID for: {encoded_path}")
        project = gl.http_get(f"/projects/{encoded_path}")
        project_id = project["id"]
        print(f"Fetched project ID: {project_id} for project: {project['name']}")
        return project_id
    except gitlab.exceptions.GitlabGetError as e:
        print(f"GitLabGetError for {project_url}: {e.response_code} - {e.error_message}")
        return None
    except Exception as e:
        print(f"Unexpected error for {project_url}: {e}")
        return None

# Metrics Functions
def get_commit_count(gl, project_id):
    print(f"Fetching commit count for project ID: {project_id}")
    try:
        project = gl.projects.get(project_id)
        commits = project.commits.list(all=True)
        count = len(commits)
        print(f"Commit count: {count}")
        return count
    except Exception as e:
        print(f"Error fetching commit count for project ID {project_id}: {e}")
        return None

def get_contributor_count(gitlab_url, private_token, project_id):
    print(f"Fetching contributor count for project ID: {project_id}")
    try:
        headers = {"PRIVATE-TOKEN": private_token}
        response = requests.get(
            f"{gitlab_url}/api/v4/projects/{project_id}/repository/contributors",
            headers=headers,
            verify=False
        )
        print(f"Contributor API response status: {response.status_code}")
        if response.status_code == 200:
            contributors = response.json()
            count = len(contributors)
            print(f"Contributor count: {count}")
            return count
        else:
            print(f"Error fetching contributors: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching contributors for project ID {project_id}: {e}")
        return None

def get_branches_count(gl, project_id):
    print(f"Fetching branch count for project ID: {project_id}")
    try:
        project = gl.projects.get(project_id)
        branches = project.branches.list(all=True)
        count = len(branches)
        print(f"Branch count: {count}")
        return count
    except Exception as e:
        print(f"Error fetching branch count for project ID {project_id}: {e}")
        return None

# Main Script
def main():
    try:
        print("Starting GitLab project metrics fetch...\n")

        # Open input and output CSV files
        with open(INPUT_FILE, mode='r') as infile, open(OUTPUT_FILE, mode='w', newline='') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + [
                "commit_count", "contributor_count", "branch_count"
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                project_url = row.get("gitlab_project_url", "").strip()
                print(f"Processing project URL: {project_url}")

                # Get project ID
                project_id = get_project_id_from_url(project_url)

                if project_id:
                    # Fetch metrics
                    commit_count = get_commit_count(gl, project_id)
                    contributor_count = get_contributor_count(GITLAB_URL, PRIVATE_TOKEN, project_id)
                    branch_count = get_branches_count(gl, project_id)

                    # Append metrics to the row
                    row.update({
                        "commit_count": commit_count,
                        "contributor_count": contributor_count,
                        "branch_count": branch_count
                    })
                else:
                    print(f"Skipping metrics fetch due to missing project ID for URL: {project_url}")

                writer.writerow(row)

        print(f"Metrics saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
