import requests
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("repoforgex.github_client")

GITHUB_API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str, user: Optional[str] = None):
        self.token = token
        self.user = user
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(requests.exceptions.RequestException))
    def repo_exists(self, owner: str, repo: str) -> bool:
        """Check if a repository exists."""
        url = f"{GITHUB_API}/repos/{owner}/{repo}"
        r = requests.get(url, headers=self.headers)
        return r.status_code == 200

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(requests.exceptions.RequestException))
    def create_repo(self, name: str, description: str = "", private: bool = True,
                    owner: Optional[str] = None) -> Dict[str, Any]:
        """Create a new repository."""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False,
        }

        if owner and owner != self.user:
            # Create in organization
            url = f"{GITHUB_API}/orgs/{owner}/repos"
        else:
            # Create in user account
            url = f"{GITHUB_API}/user/repos"

        r = requests.post(url, json=data, headers=self.headers)
        if r.status_code not in [201, 200]:
            logger.error(f"Failed to create repo: {r.status_code} {r.text}")
            r.raise_for_status()
        return r.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(requests.exceptions.RequestException))
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        url = f"{GITHUB_API}/repos/{owner}/{repo}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

