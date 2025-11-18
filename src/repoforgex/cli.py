import logging
import os
import sys
import time
from pathlib import Path

import click

from .ai_features import AutoTemplateGenerator, RepositoryHealthScorer, RepositoryNameSuggester
from .analytics import RepositoryAnalytics
from .auth.github_app import get_auth_token_from_env
from .config import load_and_validate
from .github_client import GitHubClient
from .multi_sync import push_multiple
from .scaffold import copy_template_local, ensure_minimal_files, git_init_commit_push

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("repoforgex.cli")

DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


@click.command()
@click.option("--config", "-c", default="repos.yml", help="Path to repos.yml")
@click.option(
    "--templates-dir",
    default=str(DEFAULT_TEMPLATES_DIR),
    help="Templates directory",
)
@click.option("--dry-run", is_flag=True, help="Dry run")
@click.option("--force", is_flag=True, help="Force re-init local even if exists")
@click.option("--parallel", default=4, help="Number of parallel pushes")
@click.option("--owner", default=None, help="Override owner (user/org)")
@click.option("--suggest-names", is_flag=True, help="Show AI-powered name suggestions")
@click.option(
    "--auto-templates",
    is_flag=True,
    help="Auto-generate standard templates (issues, PR, security)",
)
@click.option(
    "--health-check",
    is_flag=True,
    help="Check repository health after creation",
)
@click.option("--analytics", is_flag=True, help="Show analytics and insights")
@click.option(
    "--batch-mode",
    is_flag=True,
    help="Use batch operations with rollback capability",
)
def main(
    config,
    templates_dir,
    dry_run,
    force,
    parallel,
    owner,
    suggest_names,
    auto_templates,
    health_check,
    analytics,
    batch_mode,
):
    cfg_path = Path(config)
    try:
        cfg = load_and_validate(cfg_path)
    except Exception as e:
        logger.error("Failed to load config: %s", e)
        sys.exit(1)

    token = get_auth_token_from_env()
    if not token:
        logger.error("No authentication available. Set GITHUB_TOKEN or GitHub App envs.")
        sys.exit(1)
    user = os.environ.get("GITHUB_USER")
    client = GitHubClient(token=token, user=user)

    options = cfg.options or {}
    default_branch = options.default_branch
    commit_message = options.commit_message
    use_ssh = os.environ.get("REPOFORGEX_USE_SSH", "1" if options.use_ssh else "0") == "1"

    templates_dir = Path(templates_dir)

    # Initialize analytics tracker
    analytics_tracker = RepositoryAnalytics() if analytics else None

    tasks_for_push = []

    for entry in cfg.repos:
        name = entry.name
        desc = entry.description or ""
        private = entry.private
        tpl = entry.template
        local_path = Path(entry.path or name).resolve()
        target_owner = owner or entry.owner or user

        logger.info("Processing %s (owner=%s)", name, target_owner)

        # AI-powered name suggestions
        if suggest_names and desc:
            suggestions = RepositoryNameSuggester.suggest_names(desc, name)
            if suggestions:
                logger.info(
                    "💡 Suggested names for '%s': %s",
                    name,
                    ", ".join(suggestions),
                )

        # Check/create repo on GitHub
        exists = client.repo_exists(target_owner, name)
        if exists:
            logger.info("Repo exists: %s/%s", target_owner, name)
        else:
            if dry_run:
                logger.info(
                    "[dry-run] Would create repo: %s/%s (private=%s)",
                    target_owner,
                    name,
                    private,
                )
            else:
                logger.info("Creating repo %s/%s", target_owner, name)
                res = client.create_repo(
                    name=name,
                    description=desc,
                    private=private,
                    owner=target_owner,
                )
                logger.debug("Create response: %s", str(res)[:500])

                # Track for analytics
                if analytics_tracker:
                    analytics_tracker.add_repository(name, target_owner, private, tpl)

        # Scaffold local
        if dry_run:
            logger.info(
                "[dry-run] Would scaffold: %s (template=%s) at %s",
                name,
                tpl,
                local_path,
            )
            continue

        try:
            local_path.mkdir(parents=True, exist_ok=True)
            if tpl:
                copy_template_local(tpl, local_path, templates_dir)
            ensure_minimal_files(local_path, name, desc)

            # Auto-generate standard templates
            if auto_templates:
                logger.info("🤖 Generating standard templates for %s", name)
                github_dir = local_path / ".github"
                github_dir.mkdir(exist_ok=True)

                # Issue templates
                issue_templates_dir = github_dir / "ISSUE_TEMPLATE"
                issue_templates_dir.mkdir(exist_ok=True)
                (issue_templates_dir / "bug_report.md").write_text(
                    AutoTemplateGenerator.generate_issue_template("general")
                )

                # PR template
                (github_dir / "PULL_REQUEST_TEMPLATE.md").write_text(
                    AutoTemplateGenerator.generate_pr_template()
                )

                # Security policy
                (local_path / "SECURITY.md").write_text(
                    AutoTemplateGenerator.generate_security_policy()
                )

                # Code of conduct
                (local_path / "CODE_OF_CONDUCT.md").write_text(
                    AutoTemplateGenerator.generate_code_of_conduct()
                )

                logger.info(
                    "✓ Generated: issue templates, PR template, SECURITY.md, CODE_OF_CONDUCT.md"
                )

            # Determine remote URL
            if use_ssh:
                remote = f"git@github.com:{target_owner}/{name}.git"
            else:
                remote = f"https://github.com/{target_owner}/{name}.git"
            # Initialize and push
            if (local_path / ".git").exists() and not force:
                logger.info("Local git exists for %s (skipping init)", name)
            else:
                git_init_commit_push(
                    local_path,
                    remote_url=remote,
                    branch=default_branch,
                    message=commit_message,
                )

            # Health check
            if health_check:
                files = [
                    str(f.relative_to(local_path)) for f in local_path.rglob("*") if f.is_file()
                ]
                health_result = RepositoryHealthScorer.calculate_score(files)
                logger.info(
                    "📊 Health Score for %s: %s (%s%%) - %s",
                    name,
                    health_result["score"],
                    health_result["percentage"],
                    health_result["rating"],
                )
                if health_result["recommendations"]:
                    logger.info("Recommendations:")
                    for rec in health_result["recommendations"][:3]:
                        logger.info("  • %s", rec)

            tasks_for_push.append(
                {
                    "name": name,
                    "local_path": str(local_path),
                    "remote_url": remote,
                    "branch": default_branch,
                    "commit_message": commit_message,
                }
            )
            time.sleep(0.1)
        except Exception as e:
            logger.exception("Failed processing %s: %s", name, e)

    # Push in parallel
    if dry_run:
        logger.info("[dry-run] No push performed")
    else:
        logger.info(
            "Pushing %d repositories in parallel (workers=%s)",
            len(tasks_for_push),
            parallel,
        )
        results = push_multiple(tasks_for_push, workers=parallel)
        successes = sum(1 for r in results if r.get("success"))
        logger.info("Push summary: %s/%s", successes, len(results))

    # Display analytics if requested
    if analytics and analytics_tracker:
        logger.info("\n" + "=" * 60)
        logger.info("ANALYTICS REPORT")
        logger.info("=" * 60)
        summary = analytics_tracker.get_summary()
        logger.info("Total repositories: %s", summary.get("total_repos", 0))
        logger.info(
            "Private: %s (%.1f%%)",
            summary.get("private_repos", 0),
            summary.get("private_percentage", 0),
        )

        recommendations = analytics_tracker.get_recommendations()
        if recommendations:
            logger.info("\nRecommendations:")
            for rec in recommendations:
                logger.info("  %s", rec)

        # Export detailed report to file
        report_path = Path("repoforgex_analytics_report.txt")
        report_content = analytics_tracker.export_report(format="text")
        report_path.write_text(report_content)
        logger.info("\n✓ Detailed analytics report saved to: %s", report_path)
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
