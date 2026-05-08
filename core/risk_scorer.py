"""PR Risk Scoring.

Assigns a risk score (0.0–10.0) to a pull request based on objective
signals from the diff stats and changed file paths.

Score bands:
  0.0–2.9  → LOW    (safe to auto-merge)
  3.0–5.9  → MEDIUM (needs human review)
  6.0–7.9  → HIGH   (block auto-merge, require review)
  8.0–10.0 → CRITICAL (block + notify)

Usage::

    from core.risk_scorer import score_pull_request, RiskBand
    report = score_pull_request(files_changed=3, additions=45, deletions=10,
                                 changed_paths=["core/auth.py"])
    if report.band == RiskBand.LOW:
        merge()
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Paths whose modification carry inherent security risk
_SECURITY_SENSITIVE = re.compile(
    r"""
    (auth|oauth|jwt|token|secret|cred|password|passwd|
     permission|policy|role|admin|sudo|
     \.github/workflows|\.github/actions|
     requirements.*\.txt|pyproject\.toml|setup\.cfg|
     Dockerfile|docker-compose|\.env)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# File extensions that are higher risk when modified
_HIGH_RISK_EXTENSIONS = {
    ".sql",
    ".sh",
    ".bash",
    ".ps1",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
}
_TEST_PATH = re.compile(r"(test_|_test\.|/tests?/)", re.IGNORECASE)


def is_low_operational_risk_change(changed_paths: list[str] | None) -> bool:
    """Return True when all changed files are test/docs-only paths."""
    if not changed_paths:
        return False

    for path in changed_paths:
        normalized = path.lower()
        filename = normalized.rsplit("/", 1)[-1]
        if (
            normalized.startswith("tests/")
            or normalized.startswith("docs/")
            or normalized.endswith(".md")
            or normalized.endswith(".rst")
            or filename.startswith("test_")
            or filename.endswith("_test.py")
        ):
            continue
        return False

    return True


@dataclass
class RiskFactor:
    """A single scored risk signal."""

    name: str
    score: float  # contribution to total (0–10 scale, proportional)
    detail: str


@dataclass
class RiskReport:
    """Full risk assessment for a pull request."""

    total_score: float
    band: RiskBand
    factors: list[RiskFactor] = field(default_factory=list)
    sensitive_paths: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def blocks_auto_merge(self) -> bool:
        return self.band in (RiskBand.HIGH, RiskBand.CRITICAL)

    def as_markdown(self) -> str:
        """Render the report as a GitHub PR comment."""
        band_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "🚨"}
        emoji = band_emoji[self.band.value]
        lines = [
            f"## {emoji} Risk Assessment: "
            f"**{self.band.value}** ({self.total_score:.1f}/10)",
            "",
            self.summary,
            "",
            "### Scoring breakdown",
            "| Factor | Score |",
            "|--------|-------|",
        ]
        for f in self.factors:
            lines.append(f"| {f.name} — {f.detail} | +{f.score:.1f} |")
        if self.sensitive_paths:
            lines += [
                "",
                "### ⚠️ Security-sensitive paths modified",
                *[f"- `{p}`" for p in self.sensitive_paths],
            ]
        if self.blocks_auto_merge:
            lines += ["", "> ⛔ **Auto-merge blocked.** Manual review required."]
        else:
            lines += ["", "> ✅ Eligible for auto-merge (subject to CI passing)."]
        return "\n".join(lines)


def score_pull_request(
    files_changed: int = 0,
    additions: int = 0,
    deletions: int = 0,
    changed_paths: list[str] | None = None,
    test_coverage_delta: float = 0.0,
    pr_metadata: dict[str, Any] | None = None,
) -> RiskReport:
    """Score a pull request and return a :class:`RiskReport`.

    Args:
        files_changed: Number of files modified.
        additions: Lines added.
        deletions: Lines removed.
        changed_paths: List of file paths touched by the PR.
        test_coverage_delta: Change in coverage % (negative = coverage dropped).
        pr_metadata: Optional dict with keys: 'is_draft', 'base_branch',
            'author_association'.

    Returns:
        :class:`RiskReport` with total score and band.
    """
    changed_paths = changed_paths or []
    pr_metadata = pr_metadata or {}
    factors: list[RiskFactor] = []
    total = 0.0

    # --- 1. Change volume ---
    total_lines = additions + deletions
    if total_lines > 1000:
        s = min(3.0, 1.0 + (total_lines - 1000) / 1000)
        factors.append(RiskFactor("Change volume", s, f"{total_lines} lines changed"))
        total += s
    elif total_lines > 300:
        s = 1.5
        factors.append(RiskFactor("Change volume", s, f"{total_lines} lines changed"))
        total += s
    elif total_lines > 100:
        s = 0.5
        factors.append(RiskFactor("Change volume", s, f"{total_lines} lines changed"))
        total += s

    # --- 2. Files touched ---
    if files_changed > 30:
        s = min(2.0, 0.5 + (files_changed - 30) / 20)
        factors.append(RiskFactor("Files touched", s, f"{files_changed} files"))
        total += s
    elif files_changed > 10:
        s = 1.0
        factors.append(RiskFactor("Files touched", s, f"{files_changed} files"))
        total += s

    # --- 3. Security-sensitive paths ---
    sensitive = [p for p in changed_paths if _SECURITY_SENSITIVE.search(p)]
    if sensitive:
        s = min(4.0, 1.5 * len(sensitive))
        detail = f"{len(sensitive)} security-relevant files"
        factors.append(RiskFactor("Sensitive paths", s, detail))
        total += s

    # --- 4. High-risk file extensions ---
    risky_ext = [
        p for p in changed_paths if any(p.endswith(e) for e in _HIGH_RISK_EXTENSIONS)
    ]
    non_test_risky = [p for p in risky_ext if not _TEST_PATH.search(p)]
    if non_test_risky:
        s = min(1.5, 0.5 * len(non_test_risky))
        factors.append(
            RiskFactor(
                "Risky extensions", s, f"{len(non_test_risky)} config/script files"
            )
        )
        total += s

    # --- 5. Test coverage delta ---
    if test_coverage_delta < -10:
        s = 2.0
        factors.append(RiskFactor("Coverage drop", s, f"{test_coverage_delta:+.1f}%"))
        total += s
    elif test_coverage_delta < -2:
        s = 1.0
        factors.append(RiskFactor("Coverage drop", s, f"{test_coverage_delta:+.1f}%"))
        total += s
    elif test_coverage_delta > 5:
        # Reward for adding tests
        s = -0.5
        factors.append(RiskFactor("Coverage gain", s, f"{test_coverage_delta:+.1f}%"))
        total += s

    # --- 6. No tests modified when source changed ---
    source_files = [
        p for p in changed_paths if p.endswith(".py") and not _TEST_PATH.search(p)
    ]
    test_files = [p for p in changed_paths if _TEST_PATH.search(p)]
    if source_files and not test_files and files_changed > 0:
        s = 1.5
        factors.append(
            RiskFactor("No test changes", s, "source modified without test updates")
        )
        total += s

    # --- 7. Draft PR penalty ---
    if pr_metadata.get("is_draft"):
        s = 0.5
        factors.append(RiskFactor("Draft PR", s, "marked as draft"))
        total += s

    # --- 8. Non-default base branch ---
    base = pr_metadata.get("base_branch", "main")
    if base not in ("main", "master", "develop"):
        s = 0.5
        factors.append(RiskFactor("Non-default base", s, f"targeting '{base}'"))
        total += s

    total = max(0.0, min(10.0, total))

    if total < 3.0:
        band = RiskBand.LOW
    elif total < 6.0:
        band = RiskBand.MEDIUM
    elif total < 8.0:
        band = RiskBand.HIGH
    else:
        band = RiskBand.CRITICAL

    summary = (
        f"Analysed {files_changed} files, {additions}+ / {deletions}− lines. "
        f"{'Security-sensitive paths detected. ' if sensitive else ''}"
        f"{'Test coverage unchanged or improved. ' if test_coverage_delta >= 0 else ''}"
    ).strip()

    return RiskReport(
        total_score=round(total, 2),
        band=band,
        factors=factors,
        sensitive_paths=sensitive,
        summary=summary,
    )
