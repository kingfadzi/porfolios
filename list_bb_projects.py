from atlassian import Bitbucket

# Configuration
BITBUCKET_URL = "https://xx.yy.com"
USERNAME = "your_username"
PASSWORD = "your_app_password"  # Or use your Personal Access Token

# Initialize Bitbucket connection
bitbucket = Bitbucket(
    url=BITBUCKET_URL,
    username=USERNAME,
    password=PASSWORD,
    cloud=False,  # Set to True for Bitbucket Cloud
    verify_ssl=False
)

# Fetch all projects
def fetch_projects():
    projects = bitbucket.project_list()
    for project in projects:
        print(f"Project Key: {project['key']}, Name: {project['name']}")

# Fetch repositories for a specific project
def fetch_repositories(project_key):
    repos = bitbucket.repo_list(project_key)
    for repo in repos:
        print(f"Repo Slug: {repo['slug']}, Name: {repo['name']}, URL: {repo['links']['clone'][0]['href']}")

# Example Usage
fetch_projects()
fetch_repositories("MY_PROJECT_KEY")
