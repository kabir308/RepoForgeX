import os
import sys
import time
import logging
import click
from pathlib import Path

from .github_client import GitHubClient
from .scaffold import copy_template_local, ensure_minimal_files, git_init_commit_push
from .multi_sync import push_multiple
from .config import load_and_validate
from .auth.github_app import get_auth_token_from_env

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger("repoforgex.cli")

DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


@click.command()
@click.option("--config", "-c", default="repos.yml", help="Path to repos.yml")
@click.option("--templates-dir", default=str(DEFAULT_TEMPLATES_DIR), help="Templates directory")
@click.option("--dry-run", is_flag=True, help="Dry run")
@click.option("--force", is_flag=True, help="Force re-init local even if exists")
@click.option("--parallel", default=4, help="Number of parallel pushes")
@click.option("--owner", default=None, help="Override owner (user/org)")
def main(config, templates_dir, dry_run, force, parallel, owner):
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

    tasks_for_push = []

    for entry in cfg.repos:
        name = entry.name
        desc = entry.description or ""
        private = entry.private
        tpl = entry.template
        local_path = Path(entry.path or name).resolve()
        target_owner = owner or entry.owner or user

        logger.info("Processing %s (owner=%s)", name, target_owner)

        # Check/create repo on GitHub
        exists = client.repo_exists(target_owner, name)
        if exists:
            logger.info("Repo exists: %s/%s", target_owner, name)
        else:
            if dry_run:
                logger.info("[dry-run] Would create repo: %s/%s (private=%s)", target_owner, name, private)
            else:
                logger.info("Creating repo %s/%s", target_owner, name)
                res = client.create_repo(name=name, description=desc, private=private, owner=target_owner)
                logger.debug("Create response: %s", str(res)[:500])

        # Scaffold local
        if dry_run:
            logger.info("[dry-run] Would scaffold: %s (template=%s) at %s", name, tpl, local_path)
            continue

        try:
            local_path.mkdir(parents=True, exist_ok=True)
            if tpl:
                copy_template_local(tpl, local_path, templates_dir)
            ensure_minimal_files(local_path, name, desc)
            # Determine remote URL
            if use_ssh:
                remote = f"git@github.com:{target_owner}/{name}.git"
            else:
                remote = f"https://github.com/{target_owner}/{name}.git"
            # Initialize and push
            if (local_path / ".git").exists() and not force:
                logger.info("Local git exists for %s (skipping init)", name)
            else:
                git_init_commit_push(local_path, remote_url=remote, branch=default_branch, message=commit_message)
            tasks_for_push.append({
                "name": name,
                "local_path": str(local_path),
                "remote_url": remote,
                "branch": default_branch,
                "commit_message": commit_message
            })
            time.sleep(0.1)
        except Exception as e:
            logger.exception("Failed processing %s: %s", name, e)

    # Push in parallel
    if dry_run:
        logger.info("[dry-run] No push performed")
    else:
        logger.info("Pushing %d repositories in parallel (workers=%s)", len(tasks_for_push), parallel)
        results = push_multiple(tasks_for_push, workers=parallel)
        successes = sum(1 for r in results if r.get("success"))
        logger.info("Push summary: %s/%s", successes, len(results))


if __name__ == "__main__":
    main()

