from urllib.parse import urlparse, quote
import gitlab

# Configuration
GITLAB_URL = "https://gitlab.example.com"  # Base GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Personal access token

def get_project_id_from_url(project_url):
    try:
        print(f"Original project URL: {project_url}")

        # Parse the project path from the full URL
        parsed_url = urlparse(project_url)
        project_path = parsed_url.path.strip("/")  # Remove leading/trailing slashes
        print(f"Extracted project path: {project_path}")

        # Encode the project path for the GitLab API
        encoded_path = quote(project_path, safe="")
        print(f"Encoded project path for API: {encoded_path}")

        # Initialize GitLab client with SSL verification disabled
        print("Initializing GitLab client...")
        gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN, ssl_verify=False)

        # Fetch the project using the encoded path
        print(f"Attempting to fetch project: {encoded_path}")
        project = gl.projects.get(encoded_path)
        print(f"Project found: {project.name}")
        return project.id

    except gitlab.exceptions.GitlabGetError as e:
        print(f"GitLabGetError (HTTP {e.response_code}): {e.error_message}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Example input: full GitLab project URL
    project_url = input("Enter the GitLab project URL: ").strip()

    # Fetch the project ID
    project_id = get_project_id_from_url(project_url)

    if project_id:
        print(f"Project ID: {project_id}")
    else:
        print("Failed to fetch project ID.")
