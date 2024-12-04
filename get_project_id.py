from urllib.parse import urlparse
import gitlab

# Replace with your GitLab instance URL and private token
GITLAB_URL = "https://gitlab.example.com"
PRIVATE_TOKEN = "your_private_token"

def get_project_id_from_url(project_url):
    # Parse the URL to extract the path
    parsed_url = urlparse(project_url)
    project_path = parsed_url.path.strip("/")  # Remove leading and trailing slashes

    # Remove '.git' suffix if present
    if project_path.endswith(".git"):
        project_path = project_path[:-4]

    # Encode the project path for GitLab API
    encoded_path = project_path.replace("/", "%2F")
    print(f"Processing project path: {encoded_path}")

    # Initialize GitLab client with SSL verification disabled
    gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

    try:
        # Get project by encoded path
        project = gl.projects.get(encoded_path)
        return project.id
    except gitlab.exceptions.GitlabGetError as e:
        print(f"GitLabGetError: {e.response_code} - {e.error_message}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Example GitLab project URL
    example_url = input("Enter GitLab project URL: ").strip()
    project_id = get_project_id_from_url(example_url)

    if project_id:
        print(f"Project ID: {project_id}")
    else:
        print("Failed to fetch project ID.")
