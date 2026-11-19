"""Repository structure helpers (lightweight)."""

from __future__ import annotations

from typing import Any


def extract_paths_from_contents(contents: list[dict[str, Any]] | dict[str, Any]) -> list[str]:
    """Flatten a GitHub contents response into path list."""
    paths: list[str] = []
    if isinstance(contents, dict):
        # single file
        if "path" in contents:
            paths.append(contents["path"])
        return paths
    for item in contents:
        path = item.get("path") or item.get("name")
        if path:
            paths.append(path)
    return paths


def has_documentation(paths: list[str]) -> bool:
    lower = [p.lower() for p in paths]
    return any(
        p in ("readme.md", "readme.rst", "readme.txt", "docs", "documentation")
        or p.startswith("docs/")
        or p.endswith("/readme.md")
        for p in lower
    )


def has_tests(paths: list[str]) -> bool:
    lower = [p.lower() for p in paths]
    return any(
        p in ("tests", "test", "spec", "__tests__")
        or p.startswith("tests/")
        or p.startswith("test/")
        or "/test_" in p
        or p.endswith("_test.py")
        or p.endswith(".test.js")
        or p.endswith(".spec.ts")
        for p in lower
    )
