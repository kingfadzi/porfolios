import gitlab

# Configuration
GITLAB_URL = "https://gitlab.example.com"  # Base GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token
BASE_GROUP = "mycompany"                   # Base group name
WORKSPACE = "workspace1"                   # Workspace (subgroup name)
PROJECT_GROUP = "projectgroup"             # Project group (subgroup under workspace)
PROJECT_NAME = "project1"                  # Project name

def get_project_id(base_group, workspace, project_group, project_name):
    try:
        # Initialize GitLab client
        gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

        # Get the base group
        base_group_obj = gl.groups.get(base_group)
        print(f"Found base group: {base_group_obj.name}")

        # Find the workspace (subgroup)
        workspace_obj = next(
            (sg for sg in base_group_obj.subgroups.list(all=True) if sg.name == workspace), None
        )
        if not workspace_obj:
            print(f"Workspace '{workspace}' not found under base group '{base_group}'.")
            return None
        print(f"Found workspace: {workspace_obj.name}")

        # Find the project group (subgroup under workspace)
        project_group_obj = next(
            (sg for sg in workspace_obj.subgroups.list(all=True) if sg.name == project_group), None
        )
        if not project_group_obj:
            print(f"Project group '{project_group}' not found under workspace '{workspace}'.")
            return None
        print(f"Found project group: {project_group_obj.name}")

        # Find the project under the project group
        project_obj = next(
            (proj for proj in project_group_obj.projects.list(all=True) if proj.name == project_name), None
        )
        if not project_obj:
            print(f"Project '{project_name}' not found under project group '{project_group}'.")
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
    project_id = get_project_id(BASE_GROUP, WORKSPACE, PROJECT_GROUP, PROJECT_NAME)

    if project_id:
        print(f"Project ID: {project_id}")
    else:
        print("Failed to fetch project ID.")
