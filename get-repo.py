import gitlab

# Replace these with your GitLab details
GITLAB_URL = "https://gitlab.example.com"  # Your GitLab instance URL
PRIVATE_TOKEN = "your_private_token"       # Your personal access token
PROJECT_ID = 12345                         # Replace with your actual project ID

# Initialize the GitLab connection
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)

try:
    # Get the project
    project = gl.projects.get(PROJECT_ID)

    # Access repository statistics
    repo_stats = project.statistics
    if repo_stats:
        commit_count = repo_stats.get('commit_count', 0)
        repo_size_mb = repo_stats.get('repository_size', 0) / 1_000_000  # Convert bytes to MB

        print(f"Commit Count: {commit_count}")
        print(f"Repository Size: {repo_size_mb:.2f} MB")
    else:
        print("No statistics available for this project.")
except gitlab.exceptions.GitlabAuthenticationError:
    print("Authentication failed. Check your token and permissions.")
except gitlab.exceptions.GitlabGetError as e:
    print(f"Error fetching project details: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
