from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, validator


class RepoEntry(BaseModel):
    name: str
    description: Optional[str] = ""
    private: Optional[bool] = True
    template: Optional[str] = None
    path: Optional[str] = None
    owner: Optional[str] = None

    @validator("name")
    def name_must_be_valid(cls, v):
        if not v or " " in v:
            raise ValueError("name must be non-empty and cannot contain spaces")
        return v


class Options(BaseModel):
    default_branch: Optional[str] = Field("main")
    commit_message: Optional[str] = Field("Initial commit from RepoForgeX")
    use_ssh: Optional[bool] = Field(False)


class RepoConfig(BaseModel):
    repos: list[RepoEntry]
    options: Optional[Options] = Options()


def load_and_validate(path: Path) -> RepoConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text())
    try:
        cfg = RepoConfig(**raw)
    except ValidationError as e:
        raise RuntimeError(f"Invalid config schema: {e}")
    return cfg
