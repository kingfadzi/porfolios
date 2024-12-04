import gitlab

# Configuration
GITLAB_URL = "https://gitlab.example.com"  # Base GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token
PROJECT_GROUP_PATH = "mycompany/workspace/projectgroup"  # Path to the project group
PROJECT_NAME = "project1"                  # Project name

def get_project_id(project_group_path, project_name):
    try:
        # Initialize GitLab client
        gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

        # Get the project group
        project_group_obj = gl.groups.get(project_group_path)
        print(f"Found project group: {project_group_obj.name}")

        # Find the project under the project group
        project_obj = next(
            (proj for proj in project_group_obj.projects.list(all=True) if proj.name == project_name), None
        )
        if not project_obj:
            print(f"Project '{project_name}' not found under project group '{project_group_path}'.")
            return None

        print(f"Found project: {project_obj.name}")
        return project_obj.id

    except gitlab.exceptions.GitlabGetError as e:
        print(f"GitLabGetError: {e.response_code} - {e.error_message}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Fetch the project ID
    project_id = get_project_id(PROJECT_GROUP_PATH, PROJECT_NAME)

    if project_id:
        print(f"Project ID: {project_id}")
    else:
        print("Failed to fetch project ID.")
