"""JSON exporter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_json(data: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    return path
