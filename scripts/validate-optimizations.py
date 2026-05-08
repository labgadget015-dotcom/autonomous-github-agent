#!/usr/bin/env python3
"""
Optimization Validation Script
Validates all performance optimizations are working correctly
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import orjson

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False

try:
    import ruff

    HAS_RUFF = True
except ImportError:
    HAS_RUFF = False


class OptimizationValidator:
    """
    Validates all performance optimizations

    Checks:
    1. Required packages installed (ruff, orjson)
    2. Workflow optimizations in place
    3. Caching configured
    4. Docker optimizations
    5. Pre-commit hooks optimized
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.results: List[Tuple[str, bool, str]] = []

    def check_packages(self) -> bool:
        """Check if performance packages are installed"""
        print("📦 Checking performance packages...")

        # Check orjson
        if HAS_ORJSON:
            self.results.append(("orjson installed", True, "3-5x faster JSON"))
        else:
            self.results.append(
                ("orjson installed", False, "Install: pip install orjson")
            )

        # Check ruff
        if HAS_RUFF:
            self.results.append(("ruff installed", True, "10-100x faster linting"))
        else:
            self.results.append(("ruff installed", False, "Install: pip install ruff"))

        return HAS_ORJSON and HAS_RUFF

    def check_workflow_optimizations(self) -> bool:
        """Check workflow optimizations"""
        print("\n⚙️  Checking workflow optimizations...")

        workflow_file = (
            self.repo_root / ".github" / "workflows" / "code-quality-optimized.yml"
        )

        if not workflow_file.exists():
            self.results.append(
                ("Workflow file exists", False, "Missing workflow file")
            )
            return False

        content = workflow_file.read_text(encoding="utf-8")

        # Check for path filters
        has_paths_ignore = "paths-ignore:" in content
        self.results.append(
            (
                "Path filters configured",
                has_paths_ignore,
                "60% fewer workflow runs" if has_paths_ignore else "Add paths-ignore",
            )
        )

        # Check for shallow clones
        has_shallow_clone = "fetch-depth: 1" in content
        self.results.append(
            (
                "Shallow clones enabled",
                has_shallow_clone,
                "30-60s faster checkout" if has_shallow_clone else "Set fetch-depth: 1",
            )
        )

        # Check for enhanced caching
        has_enhanced_cache = ".mypy_cache" in content or ".pytest_cache" in content
        self.results.append(
            (
                "Enhanced caching",
                has_enhanced_cache,
                "Better cache hit rate" if has_enhanced_cache else "Add cache paths",
            )
        )

        # Check for no-cache-dir
        has_no_cache_dir = "--no-cache-dir" in content
        self.results.append(
            (
                "Pip no-cache-dir",
                has_no_cache_dir,
                "Smaller Docker images" if has_no_cache_dir else "Add --no-cache-dir",
            )
        )

        return has_paths_ignore and has_shallow_clone and has_enhanced_cache

    def check_pytest_optimizations(self) -> bool:
        """Check pytest optimizations"""
        print("\n🧪 Checking pytest optimizations...")

        pytest_file = self.repo_root / "pytest.ini"

        if not pytest_file.exists():
            self.results.append(("pytest.ini exists", False, "Missing pytest.ini"))
            return False

        content = pytest_file.read_text(encoding="utf-8")

        # Check for loadgroup
        has_loadgroup = "--dist loadgroup" in content or "--dist=loadgroup" in content
        self.results.append(
            (
                "Load group distribution",
                has_loadgroup,
                "Better load balancing" if has_loadgroup else "Add --dist loadgroup",
            )
        )

        # Check for maxfail
        has_maxfail = "--maxfail" in content
        self.results.append(
            (
                "Max failures configured",
                has_maxfail,
                "Faster failure feedback" if has_maxfail else "Add --maxfail=3",
            )
        )

        return has_loadgroup and has_maxfail

    def check_precommit_optimizations(self) -> bool:
        """Check pre-commit optimizations"""
        print("\n🔧 Checking pre-commit optimizations...")

        precommit_file = self.repo_root / ".pre-commit-config.yaml"

        if not precommit_file.exists():
            self.results.append(
                ("Pre-commit config exists", False, "Missing .pre-commit-config.yaml")
            )
            return False

        content = precommit_file.read_text(encoding="utf-8")

        # Check for fail_fast
        has_fail_fast = "fail_fast:" in content
        self.results.append(
            (
                "Fail fast enabled",
                has_fail_fast,
                "Stop on first failure" if has_fail_fast else "Add fail_fast: true",
            )
        )

        # Check for default_stages
        has_default_stages = "default_stages:" in content
        self.results.append(
            (
                "Default stages configured",
                has_default_stages,
                "Skip unnecessary runs" if has_default_stages else "Add default_stages",
            )
        )

        return has_fail_fast and has_default_stages

    def check_docker_optimizations(self) -> bool:
        """Check Docker optimizations"""
        print("\n🐳 Checking Docker optimizations...")

        dockerfile = self.repo_root / "Dockerfile"

        if not dockerfile.exists():
            self.results.append(("Dockerfile exists", False, "Missing Dockerfile"))
            return False

        content = dockerfile.read_text(encoding="utf-8")

        # Check for multi-stage build
        has_multi_stage = "FROM" in content and content.count("FROM") >= 2
        self.results.append(
            (
                "Multi-stage build",
                has_multi_stage,
                "Smaller images" if has_multi_stage else "Use multi-stage build",
            )
        )

        # Check for layer ordering
        has_ordered_layers = content.find("COPY requirements.txt") < content.find(
            "COPY *.py"
        )
        self.results.append(
            (
                "Optimized layer order",
                has_ordered_layers,
                "Better cache hits" if has_ordered_layers else "Reorder COPY commands",
            )
        )

        # Check for cache mounts
        has_cache_mounts = "--mount=type=cache" in content
        self.results.append(
            (
                "Cache mounts",
                has_cache_mounts,
                "Faster builds" if has_cache_mounts else "Add cache mounts",
            )
        )

        return has_multi_stage and has_ordered_layers and has_cache_mounts

    def check_analysis_cache(self) -> bool:
        """Check if analysis caching is configured"""
        print("\n💾 Checking analysis caching...")

        analyzer_file = (
            self.repo_root
            / ".github"
            / "scripts"
            / "parallel_code_analyzer_optimized.py"
        )

        if not analyzer_file.exists():
            self.results.append(
                ("Optimized analyzer exists", False, "Missing optimized analyzer")
            )
            return False

        content = analyzer_file.read_text(encoding="utf-8")

        # Check for ResultCache
        has_cache_class = "ResultCache" in content
        self.results.append(
            (
                "Result caching implemented",
                has_cache_class,
                "Avoid redundant analysis" if has_cache_class else "Add ResultCache",
            )
        )

        # Check for async execution
        has_async = "async def" in content
        self.results.append(
            (
                "Async execution",
                has_async,
                "Parallel tool execution" if has_async else "Use async/await",
            )
        )

        return has_cache_class and has_async

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("📊 Optimization Validation Summary")
        print("=" * 70)

        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0

        print(f"\nTotal Checks: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {percentage:.1f}%")

        print("\n✅ Passed Checks:")
        for check, success, detail in self.results:
            if success:
                print(f"  • {check}: {detail}")

        if any(not success for _, success, _ in self.results):
            print("\n❌ Failed Checks:")
            for check, success, detail in self.results:
                if not success:
                    print(f"  • {check}: {detail}")

        print("\n" + "=" * 70)

        if percentage >= 90:
            print("🎉 Excellent! Most optimizations are in place.")
        elif percentage >= 70:
            print("👍 Good! Some optimizations need attention.")
        else:
            print("⚠️  Many optimizations are missing. Review recommendations above.")

        return percentage >= 70


def main():
    """Main entry point"""
    # Get repo root - go up from scripts/ to repo root
    repo_root = Path(__file__).parent.parent.resolve()

    print("🔍 Validating Performance Optimizations\n")
    print(f"Repository: {repo_root}\n")

    validator = OptimizationValidator(repo_root)

    # Run all checks
    validator.check_packages()
    validator.check_workflow_optimizations()
    validator.check_pytest_optimizations()
    validator.check_precommit_optimizations()
    validator.check_docker_optimizations()
    validator.check_analysis_cache()

    # Print summary
    success = validator.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
