#!/usr/bin/env python3
"""Gather context from repository for AI agent processing."""

import json
import os
import sys
from pathlib import Path

def gather_repo_context():
    """Collect repository context information."""
    context = {
        "repository": os.environ.get("GITHUB_REPOSITORY", "unknown"),
        "event_name": os.environ.get("GITHUB_EVENT_NAME", "unknown"),
        "ref": os.environ.get("GITHUB_REF", "unknown"),
        "sha": os.environ.get("GITHUB_SHA", "unknown"),
        "actor": os.environ.get("GITHUB_ACTOR", "unknown"),
        "workflow": os.environ.get("GITHUB_WORKFLOW", "unknown"),
        "workspace": os.environ.get("GITHUB_WORKSPACE", "."),
    }
    
    # Get file list
    workspace = Path(context["workspace"])
    files = []
    for file_path in workspace.rglob("*"):
        if file_path.is_file() and not str(file_path).startswith("."):
            files.append(str(file_path.relative_to(workspace)))
    
    context["files"] = files[:100]  # Limit to first 100 files
    
    # Save context
    output_file = workspace / "context.json"
    with open(output_file, "w") as f:
        json.dump(context, f, indent=2)
    
    print(f"Context gathered and saved to {output_file}")
    print(json.dumps(context, indent=2))
    return context

if __name__ == "__main__":
    try:
        gather_repo_context()
        sys.exit(0)
    except Exception as e:
        print(f"Error gathering context: {e}")
        sys.exit(1)
