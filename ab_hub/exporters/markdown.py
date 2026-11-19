"""Markdown exporter."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_summary_markdown(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AB-hub Report",
        "",
        f"**Total repositories:** {report.get('total_repositories', 0)}",
        f"**Private:** {report.get('private', 0)}",
        f"**Public:** {report.get('public', 0)}",
        f"**Archived:** {report.get('archived', 0)}",
        "",
        "## Activity Classifications",
        "",
    ]
    for cls, count in (report.get("classifications") or {}).items():
        lines.append(f"- **{cls}**: {count}")
    lines += ["", "## Top Technologies", ""]
    for t in report.get("top_technologies") or []:
        lines.append(f"- {t['name']}: {t['count']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
