#!/usr/bin/env python3
"""Error handling and branching logic for workflow."""

import json
import sys
from pathlib import Path


def handle_errors():
    """Handle errors and determine branching logic."""
    print("=== Error Handler ===")

    errors = []
    warnings = []

    # Check for error files
    audit_file = Path("audit.log")
    if audit_file.exists():
        with open(audit_file, "r") as f:
            audit = json.load(f)
            violations = audit.get("violations", [])
            audit_warnings = audit.get("warnings", [])

            if violations:
                errors.extend(violations)
            if audit_warnings:
                warnings.extend(audit_warnings)

    # Check results
    results_file = Path("results.json")
    if results_file.exists():
        with open(results_file, "r") as f:
            results = json.load(f)
            if results.get("status") != "success":
                errors.append("AI agent reported non-success status")

    # Generate error report
    error_report = {
        "errors": errors,
        "warnings": warnings,
        "status": "failed" if errors else "success",
        "branch_decision": "continue" if not errors else "stop",
    }

    # Log error report
    with open("error_report.json", "w") as f:
        json.dump(error_report, f, indent=2)

    print(f"Status: {error_report['status']}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Branch decision: {error_report['branch_decision']}")

    return error_report


if __name__ == "__main__":
    try:
        report = handle_errors()
        sys.exit(0 if report["status"] == "success" else 1)
    except Exception as e:
        print(f"Error in error handler: {e}")
        sys.exit(1)
