import gitlab
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Replace these with your GitLab details
GITLAB_URL = "https://gitlab.example.com"  # GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token
PROJECT_ID = 12345                         # Replace with your project ID

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

        # Commit Count
        commit_count = get_commit_count(gl, PROJECT_ID)
        if commit_count is not None:
            print(f"Number of Commits: {commit_count}")

        # Contributor Count
        contributor_count, contributors = get_contributor_count(GITLAB_URL, PRIVATE_TOKEN, PROJECT_ID)
        if contributor_count is not None:
            print(f"Number of Contributors: {contributor_count}")
            for contributor in contributors:
                print(f"  {contributor['name']}: {contributor['commits']} commits")

        # Branch Count
        branch_count = get_branches_count(gl, PROJECT_ID)
        if branch_count is not None:
            print(f"Number of Branches: {branch_count}")

        # Tag Count
        tag_count = get_tags_count(gl, PROJECT_ID)
        if tag_count is not None:
            print(f"Number of Tags: {tag_count}")

        # Merge Requests Count
        merge_request_count = get_merge_requests_count(gl, PROJECT_ID)
        if merge_request_count is not None:
            print(f"Open Merge Requests: {merge_request_count}")

        # Pipeline Statistics
        pipeline_count, success_count, failed_count = get_pipeline_statistics(gl, PROJECT_ID)
        if pipeline_count is not None:
            print(f"Total Pipelines: {pipeline_count}")
            print(f"  Successful Pipelines: {success_count}")
            print(f"  Failed Pipelines: {failed_count}")

        # Forks and Stars
        forks_count, stars_count = get_forks_and_stars(gl, PROJECT_ID)
        if forks_count is not None:
            print(f"Forks: {forks_count}")
        if stars_count is not None:
            print(f"Stars: {stars_count}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
