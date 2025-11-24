import logging
import os
from pathlib import Path

from flask import Flask, jsonify, request

from .ai_features import AutoTemplateGenerator, RepositoryHealthScorer
from .analytics import RepositoryAnalytics
from .auth.github_app import get_auth_token_from_env
from .config import load_and_validate
from .events import get_event_emitter

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("repoforgex.web")

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify(
        {
            "name": "RepoForgeX",
            "version": "0.4.0",
            "status": "running",
            "features": [
                "GitHub App Authentication",
                "AI-Powered Repository Naming",
                "Repository Health Scoring",
                "Auto-Template Generation",
                "Advanced Analytics",
                "Batch Operations with Rollback",
                "NEOPlayer Integration",
                "CI/CD Orchestration",
            ],
        }
    )


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
        repos = [
            {
                "name": r.name,
                "description": r.description,
                "private": r.private,
            }
            for r in cfg.repos
        ]
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
            return (
                jsonify({"authenticated": False, "error": "No token available"}),
                401,
            )

        user = os.environ.get("GITHUB_USER")

        return jsonify(
            {
                "authenticated": True,
                "user": user,
                "auth_method": (
                    "GITHUB_APP" if os.environ.get("GITHUB_APP_ID") else "GITHUB_TOKEN"
                ),
            }
        )
    except Exception as e:
        logger.exception("Failed to check status")
        return jsonify({"authenticated": False, "error": str(e)}), 500


@app.route("/api/v1/health-check", methods=["POST"])
def api_health_check():
    """
    API endpoint for repository health checking.
    Accepts a list of file paths and returns health score.
    """
    try:
        data = request.get_json()
        if not data or "files" not in data:
            return jsonify({"error": "Missing 'files' in request body"}), 400

        files = data["files"]
        repository = data.get("repository", "unknown")
        developer = data.get("developer", os.environ.get("GITHUB_USER", "unknown"))

        score_data = RepositoryHealthScorer.calculate_score(files)

        # Emit event for health check
        emitter = get_event_emitter()
        if score_data["percentage"] >= 90:
            emitter.emit("health_check_excellent", developer, repository)
        elif score_data["percentage"] >= 75:
            emitter.emit("health_check_good", developer, repository)
        elif score_data["percentage"] >= 50:
            emitter.emit("health_check_fair", developer, repository)

        return jsonify(score_data)
    except Exception as e:
        logger.exception("Health check failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/analytics", methods=["GET"])
def api_analytics():
    """
    API endpoint for repository analytics.
    Returns analytics summary from the global analytics instance.
    """
    try:
        analytics = RepositoryAnalytics()
        summary = analytics.get_summary()
        recommendations = analytics.get_recommendations()

        return jsonify({"summary": summary, "recommendations": recommendations})
    except Exception as e:
        logger.exception("Analytics failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/events", methods=["GET"])
def api_events():
    """
    API endpoint for retrieving developer events.
    Returns all buffered events and statistics.
    """
    try:
        emitter = get_event_emitter()
        summary = emitter.get_event_summary()
        events = [e.to_dict() for e in emitter.get_events()]

        return jsonify({"summary": summary, "events": events})
    except Exception as e:
        logger.exception("Failed to retrieve events")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/events/developer/<developer>", methods=["GET"])
def api_developer_events(developer):
    """
    API endpoint for retrieving events for a specific developer.
    Returns XP and event history for the developer.
    """
    try:
        emitter = get_event_emitter()
        total_xp = emitter.get_total_xp(developer)
        events = [e.to_dict() for e in emitter.get_events() if e.developer == developer]

        return jsonify(
            {
                "developer": developer,
                "total_xp": total_xp,
                "event_count": len(events),
                "events": events,
            }
        )
    except Exception as e:
        logger.exception("Failed to retrieve developer events")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/templates/generate", methods=["POST"])
def api_generate_templates():
    """
    API endpoint for generating repository templates.
    Returns generated template content.
    """
    try:
        data = request.get_json()
        template_type = data.get("type", "all")
        repo_type = data.get("repo_type", "general")

        templates = {}

        if template_type in ["all", "issue"]:
            templates["issue_template"] = AutoTemplateGenerator.generate_issue_template(repo_type)

        if template_type in ["all", "pr"]:
            templates["pr_template"] = AutoTemplateGenerator.generate_pr_template()

        if template_type in ["all", "security"]:
            templates["security_policy"] = AutoTemplateGenerator.generate_security_policy()

        if template_type in ["all", "conduct"]:
            templates["code_of_conduct"] = AutoTemplateGenerator.generate_code_of_conduct()

        return jsonify(templates)
    except Exception as e:
        logger.exception("Template generation failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/cicd/webhook", methods=["POST"])
def cicd_webhook():
    """
    Webhook endpoint for CI/CD orchestration.
    Receives GitHub webhook events and processes them.
    """
    try:
        data = request.get_json()
        event_type = request.headers.get("X-GitHub-Event", "unknown")

        logger.info(f"Received CI/CD webhook: {event_type}")

        # Process different GitHub events
        if event_type == "push":
            # Handle push events
            repository = data.get("repository", {}).get("name", "unknown")
            pusher = data.get("pusher", {}).get("name", "unknown")

            emitter = get_event_emitter()
            emitter.emit(
                "repo_initialized",
                pusher,
                repository,
                {"event": "push", "ref": data.get("ref")},
            )

        elif event_type == "repository":
            # Handle repository creation
            action = data.get("action")
            repository = data.get("repository", {}).get("name", "unknown")
            sender = data.get("sender", {}).get("login", "unknown")

            if action == "created":
                emitter = get_event_emitter()
                emitter.emit("repo_created", sender, repository)

        return jsonify({"status": "processed", "event": event_type})
    except Exception as e:
        logger.exception("CI/CD webhook processing failed")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
