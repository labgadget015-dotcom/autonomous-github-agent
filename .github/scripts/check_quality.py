"""Quality ratchet: compare current ruff violations against a committed baseline.

Exit codes:
  0 — no regressions (violations per file ≤ baseline)
  1 — regressions detected (at least one file has more violations than baseline)

Usage:
  python .github/scripts/check_quality.py [--baseline .quality-baseline.json]
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path


def run_ruff(repo_root: Path) -> dict[str, int]:
    """Run ruff and return per-file violation counts (relative paths)."""
    result = subprocess.run(
        ["ruff", "check", ".", "--output-format=json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    # ruff exits 1 when violations found; that is expected
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ Failed to parse ruff JSON output.", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    root_prefix = str(repo_root) + os.sep
    counts: dict[str, int] = collections.Counter()
    for item in data:
        rel = item["filename"].replace(root_prefix, "")
        counts[rel] += 1
    return dict(counts)


def load_baseline(path: Path) -> dict[str, int]:
    """Load the committed baseline file."""
    if not path.exists():
        print(f"❌ Baseline file not found: {path}", file=sys.stderr)
        print("   Run: python .github/scripts/check_quality.py --update-baseline", file=sys.stderr)
        sys.exit(1)
    data = json.loads(path.read_text())
    return data.get("per_file", {})


def compare(current: dict[str, int], baseline: dict[str, int]) -> tuple[list[str], list[str]]:
    """Return (regressions, improvements).

    A regression is any file whose current count exceeds its baseline count.
    A new file with violations (absent from baseline) is also a regression.
    """
    all_files = set(current) | set(baseline)
    regressions: list[str] = []
    improvements: list[str] = []

    for f in sorted(all_files):
        curr = current.get(f, 0)
        base = baseline.get(f, 0)
        if curr > base:
            regressions.append(f"  ❌  {f}  ({base} → {curr}, +{curr - base})")
        elif curr < base:
            improvements.append(f"  ✅  {f}  ({base} → {curr}, -{base - curr})")

    return regressions, improvements


def update_baseline(repo_root: Path, baseline_path: Path) -> None:
    """Regenerate the baseline from the current ruff output and write it."""
    result = subprocess.run(
        ["ruff", "--version"], capture_output=True, text=True
    )
    ruff_version = result.stdout.strip().replace("ruff ", "")

    current = run_ruff(repo_root)
    data = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "ruff_version": ruff_version,
        "total_violations": sum(current.values()),
        "per_file": dict(sorted(current.items())),
    }
    baseline_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"✅ Baseline updated: {sum(current.values())} violations across {len(current)} files")
    print(f"   Written to {baseline_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        default=".quality-baseline.json",
        help="Path to baseline JSON file (default: .quality-baseline.json)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Regenerate the baseline from current state and exit 0",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    baseline_path = repo_root / args.baseline

    if args.update_baseline:
        update_baseline(repo_root, baseline_path)
        return

    baseline = load_baseline(baseline_path)
    current = run_ruff(repo_root)

    total_baseline = sum(baseline.values())
    total_current = sum(current.values())
    regressions, improvements = compare(current, baseline)

    print("=" * 60)
    print("  Quality Ratchet Report")
    print("=" * 60)
    print(f"  Baseline violations : {total_baseline}")
    print(f"  Current  violations : {total_current}")
    delta = total_current - total_baseline
    delta_str = f"+{delta}" if delta > 0 else str(delta)
    print(f"  Delta               : {delta_str}")
    print()

    if improvements:
        print(f"Improvements ({len(improvements)} file(s)):")
        print("\n".join(improvements))
        print()

    if regressions:
        print(f"Regressions ({len(regressions)} file(s)) — BLOCKING:")
        print("\n".join(regressions))
        print()
        print("Fix the regressions above, or run:")
        print("  ruff check <file> --fix")
        print()
        print("❌ Quality ratchet FAILED — this PR introduces new violations.")
        sys.exit(1)

    print("✅ Quality ratchet PASSED — no new violations introduced.")


if __name__ == "__main__":
    main()
