import os
import time
import jwt
import requests
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

GITHUB_API = "https://api.github.com"


class GitHubAppAuthError(Exception):
    pass


def _load_private_key(pem_env_or_path: str) -> str:
    """
    If pem_env_or_path is a path to a file, read it; otherwise return value (PEM content).
    """
    if not pem_env_or_path:
        raise GitHubAppAuthError("No private key provided")
    p = os.path.expanduser(pem_env_or_path)
    if os.path.exists(p):
        return open(p, "r").read()
    return pem_env_or_path


def create_jwt(app_id: str, private_key_pem: str, exp_seconds: int = 600) -> str:
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + exp_seconds, "iss": str(app_id)}
    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    # PyJWT >= 2 returns string
    return token


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(requests.exceptions.RequestException))
def get_installation_token(app_id: str, private_key_pem: str, installation_id: str) -> str:
    """
    Steps:
    1) create a JWT signed by the app private key
    2) request installation access token
    Returns installation token string.
    """
    pem = _load_private_key(private_key_pem)
    jwt_token = create_jwt(app_id, pem)
    headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
    url = f"{GITHUB_API}/app/installations/{installation_id}/access_tokens"
    r = requests.post(url, headers=headers)
    if r.status_code != 201:
        raise GitHubAppAuthError(f"Failed to obtain installation token: {r.status_code} {r.text}")
    return r.json().get("token")


def get_auth_token_from_env() -> Optional[str]:
    """
    Tries to obtain token using either GITHUB_TOKEN or GitHub App env vars.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    app_id = os.environ.get("GITHUB_APP_ID")
    private_key = os.environ.get("GITHUB_APP_PRIVATE_KEY")
    installation = os.environ.get("INSTALLATION_ID")
    if app_id and private_key and installation:
        return get_installation_token(app_id, private_key, installation)
    return None

