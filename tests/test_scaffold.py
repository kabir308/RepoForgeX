import pytest
from repoforgex.scaffold import copy_template_local, ensure_minimal_files


def test_ensure_minimal_files_creates(tmp_path):
    target = tmp_path / "proj"
    ensure_minimal_files(target, "proj-name", "desc")
    assert (target / "README.md").exists()
    assert (target / ".gitignore").exists()


def test_copy_template_missing_raises(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        copy_template_local("nonexistent", tmp_path / "target", templates_dir)

