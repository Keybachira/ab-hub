"""CSV exporter."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Sequence


def export_repositories_csv(repos: Sequence[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not repos:
        path.write_text("", encoding="utf-8")
        return path

    fieldnames = list(repos[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in repos:
            writer.writerow({k: row.get(k) for k in fieldnames})
    return path
