"""Dependency extraction from common manifests."""

from __future__ import annotations

import json
import re
from typing import Any

from ab_hub.core.logger import get_logger
from ab_hub.core.models import DependencyInfo

logger = get_logger(__name__)


def parse_package_json(content: str) -> list[DependencyInfo]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    deps: list[DependencyInfo] = []
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        section_data = data.get(section) or {}
        for name, version in section_data.items():
            deps.append(
                DependencyInfo(
                    name=name,
                    version=str(version) if version is not None else None,
                    ecosystem="npm",
                    manifest_file="package.json",
                )
            )
    return deps


def parse_requirements_txt(content: str) -> list[DependencyInfo]:
    deps: list[DependencyInfo] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Remove environment markers
        line = line.split(";")[0].strip()
        match = re.match(r"([A-Za-z0-9_.\-]+)\s*([=<>!~].+)?", line)
        if match:
            name, version = match.group(1), (match.group(2) or "").strip()
            deps.append(
                DependencyInfo(
                    name=name,
                    version=version or None,
                    ecosystem="pypi",
                    manifest_file="requirements.txt",
                )
            )
    return deps


def parse_pyproject_toml_basic(content: str) -> list[DependencyInfo]:
    """Lightweight extraction without a full TOML parser."""
    deps: list[DependencyInfo] = []
    in_project_deps = False
    in_poetry_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[project]") or stripped.startswith("[project.dependencies]"):
            # project.dependencies is an array form in PEP 621
            in_project_deps = "dependencies" in stripped or in_project_deps
            continue
        if stripped == "[project.dependencies]" or stripped.startswith("dependencies = ["):
            in_project_deps = True
            continue
        if stripped.startswith("[tool.poetry.dependencies]"):
            in_poetry_deps = True
            in_project_deps = False
            continue
        if stripped.startswith("["):
            in_project_deps = False
            in_poetry_deps = False
            continue

        if in_poetry_deps and "=" in stripped and not stripped.startswith("#"):
            parts = stripped.split("=", 1)
            name = parts[0].strip().strip("\"'")
            version = parts[1].strip().strip("\"'") if len(parts) > 1 else None
            if name and name != "python":
                deps.append(
                    DependencyInfo(
                        name=name,
                        version=version,
                        ecosystem="pypi",
                        manifest_file="pyproject.toml",
                    )
                )
        elif in_project_deps and stripped.startswith('"') or stripped.startswith("'"):
            # "package>=1.0",
            item = stripped.strip(",").strip().strip("\"'")
            match = re.match(r"([A-Za-z0-9_.\-]+)\s*([=<>!~].+)?", item)
            if match:
                name, version = match.group(1), (match.group(2) or "").strip()
                deps.append(
                    DependencyInfo(
                        name=name,
                        version=version or None,
                        ecosystem="pypi",
                        manifest_file="pyproject.toml",
                    )
                )
    return deps


def parse_go_mod(content: str) -> list[DependencyInfo]:
    deps: list[DependencyInfo] = []
    in_require = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require and stripped == ")":
            in_require = False
            continue
        if stripped.startswith("require ") and not stripped.endswith("("):
            parts = stripped[len("require ") :].split()
            if len(parts) >= 2:
                deps.append(
                    DependencyInfo(
                        name=parts[0],
                        version=parts[1],
                        ecosystem="go",
                        manifest_file="go.mod",
                    )
                )
        elif in_require and stripped and not stripped.startswith("//"):
            parts = stripped.split()
            if len(parts) >= 2:
                deps.append(
                    DependencyInfo(
                        name=parts[0],
                        version=parts[1],
                        ecosystem="go",
                        manifest_file="go.mod",
                    )
                )
    return deps


def parse_cargo_toml_basic(content: str) -> list[DependencyInfo]:
    deps: list[DependencyInfo] = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped in ("[dependencies]", "[dev-dependencies]", "[build-dependencies]"):
            in_deps = True
            continue
        if stripped.startswith("["):
            in_deps = False
            continue
        if in_deps and "=" in stripped and not stripped.startswith("#"):
            name = stripped.split("=", 1)[0].strip()
            rest = stripped.split("=", 1)[1].strip()
            version = None
            if rest.startswith('"'):
                version = rest.strip('"')
            elif "version" in rest:
                m = re.search(r'version\s*=\s*"([^"]+)"', rest)
                if m:
                    version = m.group(1)
            if name:
                deps.append(
                    DependencyInfo(
                        name=name,
                        version=version,
                        ecosystem="crates",
                        manifest_file="Cargo.toml",
                    )
                )
    return deps


def parse_composer_json(content: str) -> list[DependencyInfo]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    deps: list[DependencyInfo] = []
    for section in ("require", "require-dev"):
        for name, version in (data.get(section) or {}).items():
            if name == "php":
                continue
            deps.append(
                DependencyInfo(
                    name=name,
                    version=str(version),
                    ecosystem="composer",
                    manifest_file="composer.json",
                )
            )
    return deps


MANIFEST_PARSERS = {
    "package.json": parse_package_json,
    "requirements.txt": parse_requirements_txt,
    "pyproject.toml": parse_pyproject_toml_basic,
    "go.mod": parse_go_mod,
    "Cargo.toml": parse_cargo_toml_basic,
    "composer.json": parse_composer_json,
}


def extract_dependencies_from_files(
    files: dict[str, str],
) -> list[DependencyInfo]:
    """
    files: mapping of filename → content
    Returns deduplicated list of DependencyInfo.
    """
    all_deps: list[DependencyInfo] = []
    seen: set[tuple[str, str]] = set()
    for filename, content in files.items():
        base = filename.split("/")[-1]
        parser = MANIFEST_PARSERS.get(base)
        if not parser:
            continue
        try:
            for dep in parser(content):
                key = (dep.name.lower(), dep.ecosystem)
                if key not in seen:
                    seen.add(key)
                    all_deps.append(dep)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed parsing %s: %s", filename, exc)
    return all_deps
