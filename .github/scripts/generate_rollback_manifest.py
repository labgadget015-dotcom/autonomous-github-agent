#!/usr/bin/env python3
"""Generate rollback manifest entry for docs/ROLLBACK.md.

Called by security_scan.yml after each push to main.
Reads git metadata from environment variables set by the workflow:
  SHA, SHORT_SHA, MSG, AUTHOR, FILES_CHANGED (space-separated list)
"""

import os
from datetime import datetime, timezone


def main():
    sha = os.environ.get("SHA", "")
    short = os.environ.get("SHORT_SHA", sha[:7] if sha else "unknown")
    msg = os.environ.get("MSG", "")
    author = os.environ.get("AUTHOR", "unknown")
    files_changed = os.environ.get("FILES_CHANGED", "").split()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M timezone.utc")

    path = "docs/ROLLBACK.md"
    os.makedirs("docs", exist_ok=True)

    # Read existing content
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = "# Rollback Manifest\n\nThis file tracks all commits to main for rollback purposes.\n\n"

    # Build the new entry
    entry_lines = [
        f"## {short} — {timestamp}",
        "",
        f"- **SHA**: `{sha}`",
        f"- **Author**: {author}",
        f"- **Message**: {msg}",
        f"- **Files changed**: {len(files_changed)} file(s)",
    ]
    if files_changed:
        entry_lines.append("")
        entry_lines.append("**Changed files:**")
        for f in files_changed[:20]:  # cap at 20 files
            entry_lines.append(f"- `{f}`")
    entry_lines.append("")
    entry_lines.append("---")
    entry_lines.append("")

    new_entry = "\n".join(entry_lines) + "\n"

    # Prepend the new entry after the header
    header_end = existing.find("\n\n", existing.find("#"))
    if header_end != -1:
        new_content = (
            existing[: header_end + 2] + new_entry + existing[header_end + 2 :]
        )
    else:
        new_content = existing + new_entry

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Rollback manifest updated: {path}")
    print(f"  Commit: {short} by {author}")


if __name__ == "__main__":
    main()
