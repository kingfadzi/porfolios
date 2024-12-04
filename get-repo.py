import csv
import gitlab
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Replace these with your GitLab instance details
GITLAB_URL = "https://gitlab.example.com"  # GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token
INPUT_FILE = "input_projects.csv"          # Input CSV file with project details
OUTPUT_FILE = "output_project_metrics.csv" # Output CSV file with metrics

# Initialize the GitLab client with SSL verification disabled
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

# Metrics Functions
def get_commit_count(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        commits = project.commits.list(all=True)
        return len(commits)
    except Exception as e:
        print(f"Error fetching commit count: {e}")
        return None

def get_contributor_count(gitlab_url, private_token, project_id):
    try:
        headers = {"PRIVATE-TOKEN": private_token}
        response = requests.get(
            f"{gitlab_url}/api/v4/projects/{project_id}/repository/contributors",
            headers=headers,
            verify=False
        )
        if response.status_code == 200:
            contributors = response.json()
            return len(contributors)
        else:
            print(f"Error fetching contributors: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching contributors: {e}")
        return None

def get_branches_count(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        branches = project.branches.list(all=True)
        return len(branches)
    except Exception as e:
        print(f"Error fetching branches: {e}")
        return None

def get_tags_count(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        tags = project.tags.list(all=True)
        return len(tags)
    except Exception as e:
        print(f"Error fetching tags: {e}")
        return None

def get_merge_requests_count(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        merge_requests = project.mergerequests.list(state='opened', all=True)
        return len(merge_requests)
    except Exception as e:
        print(f"Error fetching merge requests: {e}")
        return None

def get_pipeline_statistics(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        pipelines = project.pipelines.list(all=True)
        pipeline_count = len(pipelines)
        success_count = sum(1 for p in pipelines if p.status == 'success')
        failed_count = sum(1 for p in pipelines if p.status == 'failed')
        return pipeline_count, success_count, failed_count
    except Exception as e:
        print(f"Error fetching pipelines: {e}")
        return None, None, None

def get_project_id_from_url(project_url):
    # Parse the URL
    parsed_url = urlparse(project_url)

    # Extract the path relative to the domain
    # Example: '/xxx/www/group_name/project_name' becomes 'xxx/www/group_name/project_name'
    project_path = parsed_url.path.strip("/")

    # Encode the project path for the GitLab API
    encoded_path = project_path.replace("/", "%2F")
    print(f"Attempting to fetch project ID for: {encoded_path}")

    try:
        project = gl.projects.get(encoded_path)
        return project.id
    except gitlab.exceptions.GitlabGetError as e:
        print(f"GitLabGetError for {project_url}: {e.response_code} - {e.error_message}")
        return None
    except Exception as e:
        print(f"Unexpected error for {project_url}: {e}")
        return None

# Main Script
def main():
    try:
        print("Fetching GitLab project metrics...\n")

        # Open input and output CSV files
        with open(INPUT_FILE, mode='r') as infile, open(OUTPUT_FILE, mode='w', newline='') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + [
                "commit_count", "contributor_count", "branch_count",
                "tag_count", "open_merge_requests", "total_pipelines",
                "successful_pipelines", "failed_pipelines"
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                project_url = row["gitlab_project_url"]
                project_id = get_project_id_from_url(project_url)

                if project_id:
                    # Fetch metrics
                    commit_count = get_commit_count(gl, project_id)
                    contributor_count = get_contributor_count(GITLAB_URL, PRIVATE_TOKEN, project_id)
                    branch_count = get_branches_count(gl, project_id)
                    tag_count = get_tags_count(gl, project_id)
                    merge_request_count = get_merge_requests_count(gl, project_id)
                    pipeline_count, success_count, failed_count = get_pipeline_statistics(gl, project_id)

                    # Append metrics to the row
                    row.update({
                        "commit_count": commit_count,
                        "contributor_count": contributor_count,
                        "branch_count": branch_count,
                        "tag_count": tag_count,
                        "open_merge_requests": merge_request_count,
                        "total_pipelines": pipeline_count,
                        "successful_pipelines": success_count,
                        "failed_pipelines": failed_count
                    })

                writer.writerow(row)

        print(f"Metrics saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
