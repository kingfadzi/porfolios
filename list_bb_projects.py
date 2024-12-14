import requests
import urllib3

# Suppress SSL warnings (optional)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BITBUCKET_URL = "https://xx.yy.com/rest/api/1.0/projects"
TOKEN = "your_personal_access_token"

# Headers for token-based authentication
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Make an API request
response = requests.get(
    BITBUCKET_URL,
    headers=headers,
    verify=False  # Disable SSL verification if needed
)

# Check response
if response.status_code == 200:
    print("Projects:", response.json())
else:
    print(f"Error: {response.status_code} - {response.text}")
