# (updated to keep simple but robust)
import shutil
import subprocess
from pathlib import Path


def copy_template_local(template_key: str, target: Path, templates_dir: Path):
    tpl = templates_dir / template_key
    if not tpl.exists():
        raise FileNotFoundError(f"Template '{template_key}' not found at {tpl}")
    target.mkdir(parents=True, exist_ok=True)
    for item in tpl.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def ensure_minimal_files(target: Path, name: str, description: str = ""):
    target.mkdir(parents=True, exist_ok=True)
    readme = target / "README.md"
    if not readme.exists():
        readme.write_text(f"# {name}\n\n{description}\n")
    gitignore = target / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".DS_Store\n.env\n__pycache__/\n")


def git_init_commit_push(
    local_path: Path,
    remote_url: str,
    branch: str = "main",
    message: str = "Initial commit",
):
    """Initialize git repo, commit and push to remote."""

    # Initialize git if not already initialized
    if not (local_path / ".git").exists():
        subprocess.run(["git", "init"], cwd=local_path, check=True)
        subprocess.run(["git", "checkout", "-b", branch], cwd=local_path, check=True)

    # Add remote if not exists
    result = subprocess.run(["git", "remote"], cwd=local_path, capture_output=True, text=True)
    if "origin" not in result.stdout:
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=local_path,
            check=True,
        )

    # Add all files, commit and push
    subprocess.run(["git", "add", "."], cwd=local_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", message], cwd=local_path, check=False
    )  # May fail if nothing to commit
    subprocess.run(
        ["git", "push", "-u", "origin", branch], cwd=local_path, check=False
    )  # May fail if already pushed
