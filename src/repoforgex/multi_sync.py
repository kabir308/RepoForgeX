import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logger = logging.getLogger("repoforgex.multi_sync")


def _push_one(task: dict[str, Any]) -> dict[str, Any]:
    """Push a single repository."""
    name = task.get("name")
    local_path = task.get("local_path")
    branch = task.get("branch", "main")
    commit_message = task.get("commit_message", "Initial commit")

    try:
        logger.info(f"Pushing {name} from {local_path}")

        # Add all files
        subprocess.run(
            ["git", "add", "."],
            cwd=local_path,
            check=True,
            capture_output=True,
        )

        # Commit (may fail if nothing to commit)
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            logger.warning(f"Commit failed for {name}: {result.stderr}")

        # Push
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"Push failed for {name}: {result.stderr}")
            return {"name": name, "success": False, "error": result.stderr}

        logger.info(f"Successfully pushed {name}")
        return {"name": name, "success": True}
    except Exception as e:
        logger.exception(f"Failed to push {name}: {e}")
        return {"name": name, "success": False, "error": str(e)}


def push_multiple(tasks: list[dict[str, Any]], workers: int = 4) -> list[dict[str, Any]]:
    """Push multiple repositories in parallel."""
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_push_one, task): task for task in tasks}
        for future in as_completed(futures):
            results.append(future.result())
    return results
