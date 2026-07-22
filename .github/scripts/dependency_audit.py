#!/usr/bin/env python3
"""Dependency audit against the live PyPI index.

Reads a requirements.txt, compares pinned/constrained versions to the latest
release on PyPI, and emits a categorized report (major/minor/patch) plus an
optional JSON blob for machine consumption.

Design notes:
- Stdlib only (urllib + json). No third-party deps, so it runs anywhere the
  cron host can reach PyPI -- no venv required.
- LLM/"doc auditing" enrichment is intentionally NOT done here. That is layered
  on by the Hermes orchestrator (which can call the Perplexity MCP when its key
  is valid). This script degrades gracefully to PyPI-only when no LLM is present
  -- which is the current state of this host (Perplexity key returns 401).
- Read-only by default: it queries PyPI and writes a report file. It never
  touches git or installs packages.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

PYPI_RELEASE_URL = "https://pypi.org/pypi/{name}/json"

# Match a requirement line: name [extras] [op version...]; ignore -r/-e/flags.
_REQ_LINE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~]=?.*)?\s*$")


@dataclass
class Requirement:
    name: str
    constraint: str
    current: str | None


@dataclass
class AuditResult:
    name: str
    current: str | None
    latest: str | None
    released: str | None
    category: str  # up-to-date | patch | minor | major | unknown
    notes: str = ""
    error: str | None = None


def parse_requirements(path: str | Path) -> list[Requirement]:
    """Parse a requirements.txt into Requirement objects.

    Skips blank lines, comments, and -r/-e/--flag continuation lines.
    """
    reqs: list[Requirement] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "--")):
            continue
        m = _REQ_LINE.match(line)
        if not m:
            continue
        name = m.group(1)
        spec = (m.group(2) or "").strip()
        current = None
        if spec:
            vm = re.search(r"(\d+(?:\.\d+)*)", spec)
            if vm:
                current = vm.group(1)
        reqs.append(Requirement(name=name, constraint=spec, current=current))
    return reqs


def _parse_version(v: str) -> list[int]:
    """Best-effort numeric parse; drops pre-release (+/-) suffixes."""
    nums = re.findall(r"\d+", v.split("-")[0].split("+")[0])
    return [int(n) for n in nums[:3]] if nums else [0]


def compare_versions(current: str | None, latest: str) -> str:
    if current is None:
        return "unknown"
    a = _parse_version(current)
    b = _parse_version(latest)
    if a == b:
        return "up-to-date"
    n = max(len(a), len(b))
    a += [0] * (n - len(a))
    b += [0] * (n - len(b))
    if b[0] > a[0]:
        return "major"
    if b[0] == a[0] and b[1] > a[1]:
        return "minor"
    if b[:2] == a[:2] and b[2] > a[2]:
        return "patch"
    return "minor"


def fetch_latest(
    name: str, timeout: int = 15
) -> tuple[str | None, str | None, str | None]:
    """Return (latest_version, upload_time_iso, error) for a package name."""
    url = PYPI_RELEASE_URL.format(name=name)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "gadgetlab-dep-audit/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        info = data.get("info", {})
        latest = info.get("version")
        releases = data.get("releases", {})
        released = None
        files = releases.get(latest, []) if latest else []
        if files:
            released = files[0].get("upload_time")
        return latest, released, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None, "not found on PyPI (404)"
        return None, None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 - report anything else as a string
        return None, None, str(e)


def audit(reqs: list[Requirement]) -> list[AuditResult]:
    results: list[AuditResult] = []
    for r in reqs:
        latest, released, err = fetch_latest(r.name)
        if err:
            results.append(
                AuditResult(
                    name=r.name,
                    current=r.current,
                    latest=None,
                    released=None,
                    category="unknown",
                    error=err,
                )
            )
            continue
        cat = compare_versions(r.current, latest) if latest else "unknown"
        results.append(
            AuditResult(
                name=r.name,
                current=r.current,
                latest=latest,
                released=released,
                category=cat,
            )
        )
    return results


def build_report(results: list[AuditResult], as_json: bool = False) -> str:
    if as_json:
        return json.dumps([asdict(r) for r in results], indent=2, default=str)
    by_cat: dict[str, list[AuditResult]] = {
        "major": [],
        "minor": [],
        "patch": [],
        "up-to-date": [],
        "unknown": [],
    }
    for r in results:
        by_cat.setdefault(r.category, []).append(r)
    lines = [
        "# Dependency Audit Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
    ]
    counts = {k: len(v) for k, v in by_cat.items()}
    lines.append(
        f"Total: {len(results)} | major={counts['major']} minor={counts['minor']} "
        f"patch={counts['patch']} up-to-date={counts['up-to-date']} unknown={counts['unknown']}"
    )
    for cat in ("major", "minor", "patch", "unknown"):
        if by_cat[cat]:
            lines.append(f"\n## {cat.capitalize()} updates")
            lines.append("| Package | Current | Latest | Released |")
            lines.append("|---------|---------|--------|----------|")
            for r in by_cat[cat]:
                lines.append(
                    f"| {r.name} | {r.current or '-'} | {r.latest or '-'} | {r.released or '-'} |"
                )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Audit requirements.txt against PyPI.")
    p.add_argument("--requirements", default="requirements.txt")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    p.add_argument("--report", default=None, help="Write report to this path")
    args = p.parse_args(argv)
    reqs = parse_requirements(args.requirements)
    results = audit(reqs)
    out = build_report(results, as_json=args.json)
    if args.report:
        Path(args.report).write_text(out, encoding="utf-8")
        print(f"Report written to {args.report}")
    else:
        print(out)
    # Non-zero exit on any major update so a cron wrapper can alert.
    return 2 if any(r.category == "major" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
