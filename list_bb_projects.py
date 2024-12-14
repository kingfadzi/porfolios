from atlassian import Bitbucket

# Configuration
BITBUCKET_URL = "https://xx.yy.com"  # Replace with your Bitbucket Server/DC URL
TOKEN = "your_personal_access_token"  # Replace with your Personal Access Token

# Initialize Bitbucket connection using token
bitbucket = Bitbucket(
    url=BITBUCKET_URL,
    token=TOKEN,
    cloud=False,       # Set to True if using Bitbucket Cloud
    verify_ssl=False   # Set to False to ignore SSL verification (optional)
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

if __name__ == "__main__":
    print("Fetching projects...")
    fetch_projects()

    print("\nFetching repositories for project: MY_PROJECT_KEY")
    fetch_repositories("MY_PROJECT_KEY")  # Replace with your project key
