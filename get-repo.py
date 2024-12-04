import csv
import gitlab
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Replace these with your GitLab details
GITLAB_URL = "https://gitlab.example.com"  # GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token
PROJECT_ID = 12345                         # Replace with your project ID
CSV_FILE = "gitlab_project_metrics.csv"    # Output CSV file

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
            return len(contributors), contributors
        else:
            print(f"Error fetching contributors: {response.status_code} - {response.text}")
            return None, []
    except Exception as e:
        print(f"Error fetching contributors: {e}")
        return None, []

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

def get_forks_and_stars(gl, project_id):
    try:
        project = gl.projects.get(project_id)
        return project.forks_count, project.star_count
    except Exception as e:
        print(f"Error fetching forks and stars: {e}")
        return None, None

# Main Script
def main():
    try:
        print("Fetching GitLab project metrics...\n")

        # Collect all metrics
        commit_count = get_commit_count(gl, PROJECT_ID)
        contributor_count, contributors = get_contributor_count(GITLAB_URL, PRIVATE_TOKEN, PROJECT_ID)
        branch_count = get_branches_count(gl, PROJECT_ID)
        tag_count = get_tags_count(gl, PROJECT_ID)
        merge_request_count = get_merge_requests_count(gl, PROJECT_ID)
        pipeline_count, success_count, failed_count = get_pipeline_statistics(gl, PROJECT_ID)
        forks_count, stars_count = get_forks_and_stars(gl, PROJECT_ID)

        # Prepare data for CSV
        metrics = {
            "project_id": PROJECT_ID,
            "commit_count": commit_count,
            "contributor_count": contributor_count,
            "branch_count": branch_count,
            "tag_count": tag_count,
            "open_merge_requests": merge_request_count,
            "total_pipelines": pipeline_count,
            "successful_pipelines": success_count,
            "failed_pipelines": failed_count,
            "forks": forks_count,
            "stars": stars_count,
        }

        # Write to CSV
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=metrics.keys())
            writer.writeheader()
            writer.writerow(metrics)

        print(f"Metrics saved to {CSV_FILE}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
