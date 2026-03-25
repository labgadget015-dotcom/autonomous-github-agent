#!/usr/bin/env python3
"""Generate rollback manifest entry for docs/ROLLBACK.md.

Called by security_scan.yml after each push to main.
Reads git metadata from environment variables set by the workflow:
  SHA, SHORT_SHA, MSG, AUTHOR, FILES_CHANGED (space-separated list)
  """
import os
import subprocess
from datetime import datetime, timezone

def main():
      sha = os.environ.get("SHA", "")
      short = os.environ.get("SHORT_SHA", sha[:7] if sha else "unknown")
      msg = os.environ.get("MSG", "")
      author = os.environ.get("AUTHOR", "unknown")
      files_changed_raw = os.environ.get("FILES_CHANGED", "")
      files = [f for f in files_changed_raw.split("\n") if f.strip()]

    path = "docs/ROLLBACK.md"
    os.makedirs("docs", exist_ok=True)

    if not os.path.exists(path):
              with open(path, "w") as f:
                            f.write("# Rollback Manifest\n\nAuto-generated rollback instructions for every push to main.\n\n")

          timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    file_list = "\n".join(f"- `{f}`" for f in files[:50])
    if len(files) > 50:
              file_list += f"\n- *(and {len(files) - 50} more)*"

    entry = f"""
    ---

    ## {timestamp} -- `{short}` {msg}

    **Author:** {author}

    **Rollback command:**
    ```bash
    git revert {sha} --no-edit
    git push origin main
    ```

    **Files changed:** {len(files)}

    <details><summary>File list</summary>

    {file_list}

    </details>
    """

    with open(path, "a") as f:
              f.write(entry)

    print(f"Appended rollback entry for {short}")

if __name__ == "__main__":
      main()
  
