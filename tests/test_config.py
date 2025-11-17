import pytest
from pathlib import Path
from repoforgex.config import load_and_validate, RepoConfig
from pydantic import ValidationError


def test_load_valid_config(tmp_path):
    """Test loading a valid configuration file"""
    config_file = tmp_path / "repos.yml"
    config_file.write_text("""
repos:
  - name: test-repo
    description: "Test repository"
    private: true

options:
  default_branch: main
  commit_message: "Initial commit"
  use_ssh: false
""")
    
    cfg = load_and_validate(config_file)
    assert isinstance(cfg, RepoConfig)
    assert len(cfg.repos) == 1
    assert cfg.repos[0].name == "test-repo"
    assert cfg.options.default_branch == "main"


def test_invalid_repo_name(tmp_path):
    """Test that invalid repo names are rejected"""
    config_file = tmp_path / "repos.yml"
    config_file.write_text("""
repos:
  - name: "invalid name with spaces"
    description: "This should fail"
""")
    
    with pytest.raises(RuntimeError):
        load_and_validate(config_file)


def test_missing_config_file():
    """Test that missing config file raises error"""
    with pytest.raises(FileNotFoundError):
        load_and_validate(Path("/nonexistent/repos.yml"))


def test_minimal_config(tmp_path):
    """Test minimal valid configuration"""
    config_file = tmp_path / "repos.yml"
    config_file.write_text("""
repos:
  - name: minimal-repo
""")
    
    cfg = load_and_validate(config_file)
    assert cfg.repos[0].name == "minimal-repo"
    assert cfg.repos[0].private is True  # default value
    assert cfg.options.default_branch == "main"  # default value
