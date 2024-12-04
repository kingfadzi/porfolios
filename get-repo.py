import gitlab
import requests

# Replace these with your GitLab details
GITLAB_URL = "https://gitlab.example.com"  # GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token
PROJECT_ID = 12345                         # Replace with your project ID

def get_commit_count(gl, project_id):
    try:
        # Fetch all commits
        project = gl.projects.get(project_id)
        commits = project.commits.list(all=True)  # Fetch all commits
        return len(commits)
    except Exception as e:
        print(f"Error fetching commit count: {e}")
        return None

def get_contributor_count(gitlab_url, private_token, project_id):
    try:
        # Fetch contributors using the REST API
        headers = {"PRIVATE-TOKEN": private_token}
        response = requests.get(f"{gitlab_url}/api/v4/projects/{project_id}/repository/contributors", headers=headers)

        if response.status_code == 200:
            contributors = response.json()
            return len(contributors), contributors
        else:
            print(f"Error fetching contributors: {response.status_code} - {response.text}")
            return None, []
    except Exception as e:
        print(f"Error fetching contributors: {e}")
        return None, []

def main():
    # Initialize the GitLab client
    gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)

    # Get commit count
    commit_count = get_commit_count(gl, PROJECT_ID)
    if commit_count is not None:
        print(f"Number of Commits: {commit_count}")

    # Get contributor count
    contributor_count, contributors = get_contributor_count(GITLAB_URL, PRIVATE_TOKEN, PROJECT_ID)
    if contributor_count is not None:
        print(f"Number of Contributors: {contributor_count}")
        for contributor in contributors:
            print(f"{contributor['name']}: {contributor['commits']} commits")

if __name__ == "__main__":
    main()
