#!/usr/bin/env python3
"""Enhanced context gathering with smart modes for AI agent processing."""

import json
import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Any


class ContextMode(Enum):
    """Context gathering modes based on change scope."""

    MINIMAL = "minimal"  # Only changed files
    STANDARD = "standard"  # Changed files + dependencies
    COMPREHENSIVE = "comprehensive"  # Full repo context


class SmartContextGatherer:
    """Smart context gatherer with adaptive modes."""

    def __init__(self):
        self.workspace = Path(os.environ.get("GITHUB_WORKSPACE", "."))
        self.event_name = os.environ.get("GITHUB_EVENT_NAME", "unknown")
        self.files_changed_threshold = {"minimal": 3, "standard": 10}

    def get_changed_files(self) -> list[str]:
        """Get list of changed files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip().split("\n") if result.stdout else []
        except Exception as e:
            print(f"Warning: Could not get changed files: {e}")
            return []

    def determine_context_mode(self, files_changed: list[str]) -> ContextMode:
        """Determine optimal context mode based on change scope."""
        num_files = len([f for f in files_changed if f])

        if num_files == 0:
            return ContextMode.STANDARD
        elif num_files <= self.files_changed_threshold["minimal"]:
            return ContextMode.MINIMAL
        elif num_files <= self.files_changed_threshold["standard"]:
            return ContextMode.STANDARD
        else:
            return ContextMode.COMPREHENSIVE

    def gather_minimal_context(self, changed_files: list[str]) -> dict[str, Any]:
        """Gather minimal context - only changed files."""
        return {
            "mode": "minimal",
            "files": changed_files[:50],  # Limit to 50 files
            "file_count": len(changed_files),
        }

    def gather_standard_context(self, changed_files: list[str]) -> dict[str, Any]:
        """Gather standard context - changed files + related."""
        # Get related files (same directory)
        related_files = set()
        for changed_file in changed_files:
            if changed_file:
                parent_dir = Path(changed_file).parent
                try:
                    related = list(self.workspace.glob(f"{parent_dir}/*"))
                    related_files.update(
                        str(f.relative_to(self.workspace))
                        for f in related
                        if f.is_file()
                    )
                except Exception:
                    pass

        return {
            "mode": "standard",
            "changed_files": changed_files[:50],
            "related_files": list(related_files)[:100],
            "file_count": len(changed_files),
            "related_count": len(related_files),
        }

    def gather_comprehensive_context(self) -> dict[str, Any]:
        """Gather comprehensive context - full repo."""
        files = []
        try:
            for file_path in self.workspace.rglob("*"):
                if file_path.is_file() and not any(
                    part.startswith(".") for part in file_path.parts
                ):
                    files.append(str(file_path.relative_to(self.workspace)))
        except Exception as e:
            print(f"Warning: Error gathering files: {e}")

        return {
            "mode": "comprehensive",
            "files": files[:200],  # Limit to 200 files
            "file_count": len(files),
        }

    def gather_context(self) -> dict[str, Any]:
        """Main entry point for smart context gathering."""
        # Base context
        context = {
            "repository": os.environ.get("GITHUB_REPOSITORY", "unknown"),
            "event_name": self.event_name,
            "ref": os.environ.get("GITHUB_REF", "unknown"),
            "sha": os.environ.get("GITHUB_SHA", "unknown"),
            "actor": os.environ.get("GITHUB_ACTOR", "unknown"),
            "workflow": os.environ.get("GITHUB_WORKFLOW", "unknown"),
            "workspace": str(self.workspace),
        }

        # Get changed files
        changed_files = self.get_changed_files()

        # Determine mode
        mode = self.determine_context_mode(changed_files)
        context["context_mode"] = mode.value

        # Gather context based on mode
        if mode == ContextMode.MINIMAL:
            file_context = self.gather_minimal_context(changed_files)
        elif mode == ContextMode.STANDARD:
            file_context = self.gather_standard_context(changed_files)
        else:
            file_context = self.gather_comprehensive_context()

        context.update(file_context)

        # Calculate estimated token usage
        context["estimated_tokens"] = self._estimate_tokens(context)

        # Save context
        output_file = self.workspace / "context.json"
        with open(output_file, "w") as f:
            json.dump(context, f, indent=2)

        print(f"✅ Context gathered in {mode.value} mode")
        print(f"📊 Files: {context.get('file_count', 0)}")
        print(f"🎯 Estimated tokens: {context.get('estimated_tokens', 0)}")
        print(json.dumps(context, indent=2))

        return context

    def _estimate_tokens(self, context: dict[str, Any]) -> int:
        """Estimate token usage for context."""
        # Rough estimation: 1 token ≈ 4 characters
        context_str = json.dumps(context)
        return len(context_str) // 4


if __name__ == "__main__":
    try:
        gatherer = SmartContextGatherer()
        gatherer.gather_context()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error gathering context: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
