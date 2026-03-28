"""Error handling, branching logic, and cleanup for workflow."""

import json
import sys
import logging
from pathlib import Path

# Configure logging for better traceability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handle_errors():
    """Handle errors, determine branching logic, and clean up input files."""
    logger.info("Starting error handler execution.")

    errors = []
    warnings = []
    results_file = Path("results.json")

    # 1. Process Results
    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)

            if results.get("status") != "success":
                errors.append("AI agent reported non-success status")

            # 2. Cleanup: Remove the file after successful processing
            results_file.unlink()
            logger.info(f"Successfully processed and removed {results_file}")

        except (json.JSONDecodeError, IOError) as e:
            errors.append(f"Failed to process results file: {e}")
            logger.error(f"File processing error: {e}")
    else:
        warnings.append("results.json not found; skipping result validation.")
        logger.warning("results.json not found.")

    # 3. Generate Report
    error_report = {
        "errors": errors,
        "warnings": warnings,
        "status": "failed" if errors else "success",
        "branch_decision": "continue" if not errors else "stop"
    }

    # 4. Save and Log Status
    report_path = Path("error_report.json")
    with open(report_path, "w") as f:
        json.dump(error_report, f, indent=2)

    logger.info(f"Report generated: Status={error_report['status']}, "
                f"Decision={error_report['branch_decision']}")

    if errors:
        for err in errors:
            logger.error(f"Error encountered: {err}")

    return error_report

if __name__ == "__main__":
    try:
        report = handle_errors()
        sys.exit(0 if report["status"] == "success" else 1)
    except Exception as e:
        logger.critical(f"Unhandled exception in error handler: {e}")
        sys.exit(1)
