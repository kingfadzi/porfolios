import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Config class for accessing environment variables with defaults.
    """
    # Environment variables with sensible defaults
    RULESET_MAPPING_FILE = os.getenv("RULESET_MAPPING_FILE", "./tools/semgrep/language_ruleset_map.txt")
    METRICS_DATABASE_USER = os.getenv("METRICS_DATABASE_USER", "postgres")
    METRICS_DATABASE_PASSWORD = os.getenv("METRICS_DATABASE_PASSWORD", "postgres")
    METRICS_DATABASE_HOST = os.getenv("METRICS_DATABASE_HOST", "192.168.1.188")
    METRICS_DATABASE_PORT = os.getenv("METRICS_DATABASE_PORT", "5422")
    METRICS_DATABASE_NAME = os.getenv("METRICS_DATABASE_NAME", "gitlab-usage")
    CLONED_REPOSITORIES_DIR = os.getenv("CLONED_REPOSITORIES_DIR", "/tmp/cloned_repositories")
    TRIVYIGNORE_TEMPLATE = os.getenv("TRIVYIGNORE_TEMPLATE", "/tools/trivy/.trivyignore")
    SYFT_CONFIG_PATH = os.getenv("SYFT_CONFIG_PATH", "/root/.syft/config.yaml")
    GRYPE_CONFIG_PATH = os.getenv("GRYPE_CONFIG_PATH", "/root/.grype/config.yaml")
    SEMGREP_RULESET = os.getenv("SEMGREP_RULESET", "./tools/semgrep/semgre-rules")
