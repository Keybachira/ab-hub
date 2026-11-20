"""Technology detection from languages API + file signatures."""

from __future__ import annotations

from typing import Any

from ab_hub.core.models import DetectionMethod, TechnologyCategory, TechnologyInfo
from ab_hub.core.logger import get_logger

logger = get_logger(__name__)

# File signature → technology mapping
FILE_SIGNATURES: dict[str, tuple[str, TechnologyCategory]] = {
    "package.json": ("Node.js", TechnologyCategory.RUNTIME),
    "tsconfig.json": ("TypeScript", TechnologyCategory.LANGUAGE),
    "next.config.js": ("Next.js", TechnologyCategory.FRAMEWORK),
    "next.config.mjs": ("Next.js", TechnologyCategory.FRAMEWORK),
    "next.config.ts": ("Next.js", TechnologyCategory.FRAMEWORK),
    "vite.config.js": ("Vite", TechnologyCategory.TOOL),
    "vite.config.ts": ("Vite", TechnologyCategory.TOOL),
    "requirements.txt": ("Python", TechnologyCategory.LANGUAGE),
    "pyproject.toml": ("Python", TechnologyCategory.LANGUAGE),
    "Pipfile": ("Python", TechnologyCategory.LANGUAGE),
    "pubspec.yaml": ("Flutter/Dart", TechnologyCategory.FRAMEWORK),
    "Cargo.toml": ("Rust", TechnologyCategory.LANGUAGE),
    "go.mod": ("Go", TechnologyCategory.LANGUAGE),
    "composer.json": ("PHP", TechnologyCategory.LANGUAGE),
    "Dockerfile": ("Docker", TechnologyCategory.CONTAINER),
    "docker-compose.yml": ("Docker Compose", TechnologyCategory.CONTAINER),
    "docker-compose.yaml": ("Docker Compose", TechnologyCategory.CONTAINER),
    ".github/workflows": ("GitHub Actions", TechnologyCategory.CI),
    "Gemfile": ("Ruby", TechnologyCategory.LANGUAGE),
    "pom.xml": ("Java/Maven", TechnologyCategory.LANGUAGE),
    "build.gradle": ("Java/Gradle", TechnologyCategory.LANGUAGE),
    "build.gradle.kts": ("Kotlin/Gradle", TechnologyCategory.LANGUAGE),
    "Package.swift": ("Swift", TechnologyCategory.LANGUAGE),
    "mix.exs": ("Elixir", TechnologyCategory.LANGUAGE),
    "Cargo.lock": ("Rust", TechnologyCategory.LANGUAGE),
    "pnpm-lock.yaml": ("pnpm", TechnologyCategory.PACKAGE_MANAGER),
    "yarn.lock": ("Yarn", TechnologyCategory.PACKAGE_MANAGER),
    "package-lock.json": ("npm", TechnologyCategory.PACKAGE_MANAGER),
}


def detect_from_languages(languages: dict[str, int]) -> list[TechnologyInfo]:
    """Convert GitHub languages API response into TechnologyInfo list."""
    total = sum(languages.values()) or 1
    results: list[TechnologyInfo] = []
    for name, bytes_count in languages.items():
        confidence = min(1.0, bytes_count / total + 0.3)
        results.append(
            TechnologyInfo(
                name=name,
                category=TechnologyCategory.LANGUAGE,
                detection_method=DetectionMethod.GITHUB_LANGUAGES,
                confidence=round(confidence, 2),
                evidence=f"{bytes_count} bytes",
                bytes=bytes_count,
            )
        )
    return results


def detect_from_file_tree(paths: list[str]) -> list[TechnologyInfo]:
    """Detect technologies from file / directory names present in the repo."""
    found: dict[str, TechnologyInfo] = {}
    lower_paths = [p.lower() for p in paths]

    for signature, (tech_name, category) in FILE_SIGNATURES.items():
        sig_lower = signature.lower()
        matched = any(
            p == sig_lower or p.endswith("/" + sig_lower) or sig_lower in p
            for p in lower_paths
        )
        if matched and tech_name not in found:
            found[tech_name] = TechnologyInfo(
                name=tech_name,
                category=category,
                detection_method=DetectionMethod.FILE_SIGNATURE,
                confidence=0.9,
                evidence=f"Found signature: {signature}",
            )
    return list(found.values())


def merge_technologies(*groups: list[TechnologyInfo]) -> list[TechnologyInfo]:
    """Merge detections, preferring higher confidence / more specific methods."""
    by_name: dict[str, TechnologyInfo] = {}
    for group in groups:
        for tech in group:
            existing = by_name.get(tech.name)
            if existing is None or tech.confidence > existing.confidence:
                by_name[tech.name] = tech
    return list(by_name.values())
