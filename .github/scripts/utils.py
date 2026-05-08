"""Utility functions for GitHub workflow automation.

This module provides common utility functions used across GitHub Actions workflows
for code quality analysis, security scanning, and CI/CD pipeline operations.
"""

import json
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: str | Path) -> dict | None:
    """Load and parse a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dict containing the parsed JSON data, or None if file not found

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        logger.error(f"Invalid JSON in {file_path}: {error}")
        raise
    except Exception as error:
        logger.error(f"Error loading {file_path}: {error}")
        return None


def save_json_file(data: dict, file_path: str | Path) -> bool:
    """Save data to a JSON file.

    Args:
        data: Dictionary to save as JSON
        file_path: Path where the file should be saved

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as error:
        logger.error(f"Error saving {file_path}: {error}")
        return False


def get_env_variable(name: str, default: str | None = None) -> str | None:
    """Get an environment variable with optional default.

    Args:
        name: Name of the environment variable
        default: Default value if variable is not set

    Returns:
        Value of the environment variable or default
    """
    value = os.getenv(name, default)
    if value is None:
        logger.debug(f"Environment variable {name} not set")
    return value


def calculate_quality_score(
    pylint_issues: int = 0,
    flake8_issues: int = 0,
    security_high: int = 0,
    security_medium: int = 0,
) -> float:
    """Calculate an overall code quality score.

    Args:
        pylint_issues: Number of Pylint issues found
        flake8_issues: Number of Flake8 issues found
        security_high: Number of high severity security issues
        security_medium: Number of medium severity security issues

    Returns:
        Quality score from 0.0 to 10.0
    """
    base_score = 10.0

    # Deduct points for issues
    base_score -= min(pylint_issues * 0.1, 3.0)
    base_score -= min(flake8_issues * 0.1, 3.0)
    base_score -= min(security_high * 1.0, 2.0)
    base_score -= min(security_medium * 0.3, 1.0)

    return max(0.0, base_score)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def find_files_by_extension(directory: str | Path, extension: str) -> list[Path]:
    """Find all files with a specific extension in a directory.

    Args:
        directory: Directory to search
        extension: File extension (e.g., '.py', '.json')

    Returns:
        List of Path objects for matching files
    """
    try:
        path = Path(directory)
        if not path.exists():
            logger.warning(f"Directory not found: {directory}")
            return []

        return list(path.rglob(f"*{extension}"))
    except Exception as error:
        logger.error(f"Error searching {directory}: {error}")
        return []


def validate_threshold(
    value: float, threshold: float, higher_is_better: bool = True
) -> bool:
    """Validate if a value meets a threshold requirement.

    Args:
        value: The value to check
        threshold: The threshold to compare against
        higher_is_better: If True, value must be >= threshold; otherwise <= threshold

    Returns:
        True if threshold is met, False otherwise
    """
    if higher_is_better:
        return value >= threshold
    return value <= threshold


if __name__ == "__main__":
    # Example usage
    score = calculate_quality_score(
        pylint_issues=5, flake8_issues=3, security_high=0, security_medium=2
    )
    print(f"Quality Score: {score:.2f}/10.0")
