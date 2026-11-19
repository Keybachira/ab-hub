"""Domain models (Pydantic) used across the application."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class ActivityClassification(str, Enum):
    ACTIVE = "Active"
    MAINTAINED = "Maintained"
    DORMANT = "Dormant"
    POSSIBLY_ABANDONED = "Possibly Abandoned"
    ARCHIVED = "Archived"


class DetectionMethod(str, Enum):
    GITHUB_LANGUAGES = "github_languages"
    FILE_SIGNATURE = "file_signature"
    DEPENDENCY_MANIFEST = "dependency_manifest"
    INFERRED = "inferred"


class TechnologyCategory(str, Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    LIBRARY = "library"
    TOOL = "tool"
    RUNTIME = "runtime"
    PACKAGE_MANAGER = "package_manager"
    CI = "ci"
    CONTAINER = "container"
    OTHER = "other"


class RepositoryMeta(BaseModel):
    """Lightweight repository metadata from GitHub."""

    github_id: int
    name: str
    full_name: str
    owner: str
    description: str | None = None
    visibility: Visibility = Visibility.PUBLIC
    default_branch: str | None = "main"
    html_url: str
    clone_url: str | None = None
    is_fork: bool = False
    is_archived: bool = False
    is_private: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    pushed_at: datetime | None = None
    size: int = 0
    language: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0


class CommitInfo(BaseModel):
    sha: str
    message: str
    author: str | None = None
    author_date: datetime | None = None
    committer_date: datetime | None = None


class BranchInfo(BaseModel):
    name: str
    commit_sha: str
    is_default: bool = False


class TechnologyInfo(BaseModel):
    name: str
    category: TechnologyCategory = TechnologyCategory.OTHER
    detection_method: DetectionMethod
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    evidence: str | None = None
    bytes: int | None = None  # for languages


class DependencyInfo(BaseModel):
    name: str
    version: str | None = None
    ecosystem: str
    manifest_file: str


class ActivityScore(BaseModel):
    score: float = Field(ge=0.0, le=100.0)
    classification: ActivityClassification
    evidence: dict[str, Any] = Field(default_factory=dict)
    commits_7d: int = 0
    commits_30d: int = 0
    commits_90d: int = 0
    last_commit_at: datetime | None = None
    avg_days_between_commits: float | None = None


class ScanResult(BaseModel):
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "running"
    repositories_discovered: int = 0
    repositories_analyzed: int = 0
    errors: list[str] = Field(default_factory=list)
