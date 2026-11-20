"""Security / vulnerability intelligence.

Uses the public OSV (Open Source Vulnerabilities) API as primary source.
Optionally enriches with GitHub Dependabot alerts when the token has access.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from ab_hub.core.logger import get_logger
from ab_hub.core.models import DependencyInfo

logger = get_logger(__name__)

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
OSV_QUERYBATCH_URL = "https://api.osv.dev/v1/querybatch"

# Map our ecosystem names → OSV ecosystem identifiers
ECOSYSTEM_MAP: dict[str, str] = {
    "npm": "npm",
    "pypi": "PyPI",
    "pip": "PyPI",
    "python": "PyPI",
    "go": "Go",
    "golang": "Go",
    "crates": "crates.io",
    "rust": "crates.io",
    "maven": "Maven",
    "java": "Maven",
    "nuget": "NuGet",
    "rubygems": "RubyGems",
    "composer": "Packagist",
    "php": "Packagist",
    "pub": "Pub",
    "dart": "Pub",
}


def normalize_ecosystem(eco: str) -> str | None:
    return ECOSYSTEM_MAP.get(eco.lower().strip())


def _severity_from_osv(vuln: dict[str, Any]) -> tuple[str, float | None]:
    """Extract best-effort severity and CVSS score from an OSV record."""
    # Prefer database_specific severity (GitHub, etc.)
    db_specific = vuln.get("database_specific") or {}
    severity = (db_specific.get("severity") or "").upper()
    if severity in ("CRITICAL", "HIGH", "MEDIUM", "MODERATE", "LOW"):
        if severity == "MODERATE":
            severity = "MEDIUM"
        return severity, db_specific.get("cvss_score")

    # Fallback: CVSS from severity array
    for entry in vuln.get("severity") or []:
        if entry.get("type") == "CVSS_V3":
            score = entry.get("score")
            # score can be a vector string; try to parse numeric if present
            try:
                # Some responses put numeric score elsewhere
                numeric = float(db_specific.get("cvss") or 0)
            except (TypeError, ValueError):
                numeric = None
            return "UNKNOWN", numeric

    return "UNKNOWN", None


def _fixed_version(vuln: dict[str, Any], package_name: str, ecosystem: str) -> str | None:
    """Try to find the earliest fixed version for this package."""
    for affected in vuln.get("affected") or []:
        pkg = affected.get("package") or {}
        if pkg.get("name") == package_name and pkg.get("ecosystem") == ecosystem:
            for r in affected.get("ranges") or []:
                if r.get("type") == "ECOSYSTEM":
                    for event in r.get("events") or []:
                        if "fixed" in event:
                            return event["fixed"]
    return None


def _extract_ids(vuln: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    osv_id = vuln.get("id")
    ghsa_id = None
    cve_id = None
    for alias in vuln.get("aliases") or []:
        if alias.startswith("GHSA-"):
            ghsa_id = alias
        elif alias.startswith("CVE-"):
            cve_id = alias
    # Also check related
    for rel in vuln.get("related") or []:
        if rel.startswith("GHSA-") and not ghsa_id:
            ghsa_id = rel
        elif rel.startswith("CVE-") and not cve_id:
            cve_id = rel
    return osv_id, ghsa_id, cve_id


async def query_osv_single(
    client: httpx.AsyncClient,
    package_name: str,
    ecosystem: str,
    version: str | None = None,
) -> list[dict[str, Any]]:
    """Query OSV for a single package (+ optional version)."""
    osv_eco = normalize_ecosystem(ecosystem)
    if not osv_eco:
        return []

    payload: dict[str, Any] = {
        "package": {"name": package_name, "ecosystem": osv_eco},
    }
    if version and version not in ("*", "latest", ""):
        # Strip common version prefixes/ranges for better matching
        clean = version.lstrip("=^~>< ")
        # Take first token if range
        clean = clean.split(",")[0].split(" ")[0].strip()
        if clean:
            payload["version"] = clean

    try:
        resp = await client.post(OSV_QUERY_URL, json=payload, timeout=20.0)
        if resp.status_code != 200:
            logger.debug("OSV query failed (%s): %s", resp.status_code, resp.text[:200])
            return []
        data = resp.json()
        return data.get("vulns") or []
    except Exception as exc:  # noqa: BLE001
        logger.debug("OSV request error for %s: %s", package_name, exc)
        return []


async def query_osv_batch(
    client: httpx.AsyncClient,
    packages: list[tuple[str, str, str | None]],
) -> list[list[dict[str, Any]]]:
    """
    Batch query OSV.
    packages = list of (name, ecosystem, version)
    Returns list of vuln-lists aligned with input order.
    """
    queries = []
    valid_indices: list[int] = []
    for i, (name, eco, ver) in enumerate(packages):
        osv_eco = normalize_ecosystem(eco)
        if not osv_eco:
            continue
        q: dict[str, Any] = {"package": {"name": name, "ecosystem": osv_eco}}
        if ver and ver not in ("*", "latest", ""):
            clean = ver.lstrip("=^~>< ").split(",")[0].split(" ")[0].strip()
            if clean:
                q["version"] = clean
        queries.append(q)
        valid_indices.append(i)

    results: list[list[dict[str, Any]]] = [[] for _ in packages]
    if not queries:
        return results

    # OSV batch has a practical size limit; chunk if needed
    chunk_size = 50
    for start in range(0, len(queries), chunk_size):
        chunk = queries[start : start + chunk_size]
        chunk_indices = valid_indices[start : start + chunk_size]
        try:
            resp = await client.post(
                OSV_QUERYBATCH_URL,
                json={"queries": chunk},
                timeout=45.0,
            )
            if resp.status_code != 200:
                logger.warning("OSV batch failed: %s", resp.status_code)
                continue
            data = resp.json()
            for offset, item in enumerate(data.get("results") or []):
                idx = chunk_indices[offset]
                results[idx] = item.get("vulns") or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("OSV batch error: %s", exc)

    return results


def osv_to_finding(
    vuln: dict[str, Any],
    package_name: str,
    ecosystem: str,
    installed_version: str | None,
) -> dict[str, Any]:
    """Convert an OSV vulnerability record into a normalized finding dict."""
    severity, cvss = _severity_from_osv(vuln)
    osv_id, ghsa_id, cve_id = _extract_ids(vuln)
    fixed = _fixed_version(vuln, package_name, normalize_ecosystem(ecosystem) or ecosystem)

    published = None
    modified = None
    try:
        if vuln.get("published"):
            published = datetime.fromisoformat(vuln["published"].replace("Z", "+00:00"))
        if vuln.get("modified"):
            modified = datetime.fromisoformat(vuln["modified"].replace("Z", "+00:00"))
    except Exception:
        pass

    return {
        "osv_id": osv_id,
        "ghsa_id": ghsa_id,
        "cve_id": cve_id,
        "package_name": package_name,
        "ecosystem": ecosystem,
        "installed_version": installed_version,
        "severity": severity,
        "summary": (vuln.get("summary") or "")[:1000] or None,
        "details": (vuln.get("details") or "")[:4000] or None,
        "fixed_version": fixed,
        "published_at": published,
        "modified_at": modified,
        "source": "osv",
        "cvss_score": cvss,
        "is_direct": True,
    }


async def scan_dependencies_for_vulns(
    dependencies: list[DependencyInfo],
    *,
    max_concurrency: int = 10,
) -> list[dict[str, Any]]:
    """
    Check a list of DependencyInfo against OSV and return normalized findings.
    """
    if not dependencies:
        return []

    packages = [(d.name, d.ecosystem, d.version) for d in dependencies]
    findings: list[dict[str, Any]] = []

    async with httpx.AsyncClient(
        headers={"User-Agent": "AB-hub/0.1.0 (security-scanner)"},
        follow_redirects=True,
    ) as client:
        # Prefer batch
        batch_results = await query_osv_batch(client, packages)

        for dep, vulns in zip(dependencies, batch_results):
            for v in vulns:
                findings.append(osv_to_finding(v, dep.name, dep.ecosystem, dep.version))

    # Deduplicate by (osv_id or cve_id, package_name)
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for f in findings:
        key = f"{f.get('osv_id') or f.get('cve_id') or f.get('summary')}:{f['package_name']}"
        if key not in seen:
            seen.add(key)
            unique.append(f)

    logger.info(
        "Security scan: %d dependencies → %d unique vulnerability findings",
        len(dependencies),
        len(unique),
    )
    return unique


# Severity ordering for sorting / scoring
SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}


def security_score(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce a simple security summary score from findings."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for f in findings:
        sev = (f.get("severity") or "UNKNOWN").upper()
        if sev not in counts:
            sev = "UNKNOWN"
        counts[sev] += 1

    # Simple risk points
    risk = (
        counts["CRITICAL"] * 40
        + counts["HIGH"] * 20
        + counts["MEDIUM"] * 8
        + counts["LOW"] * 2
        + counts["UNKNOWN"] * 1
    )
    # Cap and invert into a 0-100 "security health" score
    health = max(0, 100 - min(100, risk))

    if counts["CRITICAL"] > 0:
        status = "Critical"
    elif counts["HIGH"] > 0:
        status = "High Risk"
    elif counts["MEDIUM"] > 0:
        status = "Medium Risk"
    elif counts["LOW"] > 0 or counts["UNKNOWN"] > 0:
        status = "Low Risk"
    else:
        status = "Clean"

    return {
        "health_score": health,
        "status": status,
        "counts": counts,
        "total": sum(counts.values()),
    }
