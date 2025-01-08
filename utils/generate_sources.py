import re
import requests
from bs4 import BeautifulSoup


def find_github_repos(url):
    """
    Fetch the webpage at `url`, parse the HTML with BeautifulSoup,
    and return a set of GitHub repository URLs.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError if the response is unsuccessful
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return set()

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract all hrefs from <a> tags
    hrefs = [link.get("href") for link in soup.find_all("a") if link.get("href")]

    # Also check any raw text for patterns (e.g., plain text links)
    page_text = soup.get_text().split()
    hrefs.extend(page_text)

    # Regex pattern to match GitHub repository URLs
    pattern = re.compile(
        r'(?:https|git)(?::\/\/|@)github\.com[:\/]([\w\-]+)/([\w\-\.]+)(?:\.git)?',
        re.IGNORECASE
    )

    # Store unique matches
    matched_repos = set()
    for item in hrefs:
        match = pattern.search(item)
        if match:
            username = match.group(1)
            repo = match.group(2)
            canonical_url = f"https://github.com/{username}/{repo}"
            matched_repos.add(canonical_url)

    return matched_repos


def process_urls(file_path, output_path):
    """
    Process a list of URLs from a file and write the found GitHub repos to an output file.
    """
    try:
        with open(file_path, "r") as file:
            urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return

    # Create an output set to store unique repositories
    all_repos = set()

    for url in urls:
        print(f"Processing URL: {url}")
        repos = find_github_repos(url)
        if repos:
            print(f"Found {len(repos)} repos for {url}.")
            all_repos.update(repos)

    # Write the results to the output file
    with open(output_path, "w") as output_file:
        for repo in sorted(all_repos):
            output_file.write(repo + "\n")

    print(f"\nExtracted {len(all_repos)} unique GitHub repositories.")
    print(f"Results written to '{output_path}'.")


if __name__ == "__main__":
    # Input file containing list of URLs (one per line)
    input_file = input("Enter the path to the input file with source URLs: ").strip()
    
    # Output file to store found repositories
    output_file = input("Enter the path to save the output repositories: ").strip()

    # Process the URLs and extract GitHub repositories
    process_urls(input_file, output_file)