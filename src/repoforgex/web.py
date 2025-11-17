import os
import logging
from flask import Flask, jsonify
from pathlib import Path

from .config import load_and_validate
from .github_client import GitHubClient
from .auth.github_app import get_auth_token_from_env

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger("repoforgex.web")

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({
        "name": "RepoForgeX",
        "version": "0.2.0",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/repos", methods=["GET"])
def list_repos():
    """List configured repositories from repos.yml"""
    try:
        config_path = Path(os.environ.get("CONFIG_PATH", "repos.yml"))
        if not config_path.exists():
            return jsonify({"error": "Config file not found"}), 404

        cfg = load_and_validate(config_path)
        repos = [{"name": r.name, "description": r.description, "private": r.private} for r in cfg.repos]
        return jsonify({"repos": repos, "count": len(repos)})
    except Exception as e:
        logger.exception("Failed to list repos")
        return jsonify({"error": str(e)}), 500


@app.route("/status")
def status():
    """Check authentication status"""
    try:
        token = get_auth_token_from_env()
        if not token:
            return jsonify({"authenticated": False, "error": "No token available"}), 401

        user = os.environ.get("GITHUB_USER")

        return jsonify({
            "authenticated": True,
            "user": user,
            "auth_method": "GITHUB_APP" if os.environ.get("GITHUB_APP_ID") else "GITHUB_TOKEN"
        })
    except Exception as e:
        logger.exception("Failed to check status")
        return jsonify({"authenticated": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

