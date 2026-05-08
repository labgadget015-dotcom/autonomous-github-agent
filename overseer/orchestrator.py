#!/usr/bin/env python3
"""
Repository Overseer Orchestrator

Main orchestration engine for repository management and improvement.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .automation_engine import AutomationEngine
from .cicd_optimizer import CICDOptimizer
from .code_analyzer import CodeAnalyzer
from .dependency_manager import DependencyManager
from .doc_generator import DocumentationGenerator
from .issue_triager import IssueTriager
from .monitor import RepositoryMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RepositoryOverseer:
    """
    Advanced full-stack repository overseer that manages and improves repositories.

    Features:
    - Deep code analysis and refactoring recommendations
    - Automated documentation generation
    - Smart dependency management
    - CI/CD workflow optimization
    - Intelligent issue triaging
    - Automation script generation
    - Real-time monitoring and recommendations
    """

    def __init__(self, repo_path: str, config: dict | None = None):
        """
        Initialize the repository overseer.

        Args:
            repo_path: Path to the repository root
            config: Optional configuration dictionary
        """
        self.repo_path = Path(repo_path)
        self.config = config or self._load_default_config()

        # Initialize components
        self.code_analyzer = CodeAnalyzer(self.repo_path, self.config)
        self.doc_generator = DocumentationGenerator(self.repo_path, self.config)
        self.dependency_manager = DependencyManager(self.repo_path, self.config)
        self.cicd_optimizer = CICDOptimizer(self.repo_path, self.config)
        self.issue_triager = IssueTriager(self.repo_path, self.config)
        self.automation_engine = AutomationEngine(self.repo_path, self.config)
        self.monitor = RepositoryMonitor(self.repo_path, self.config)

        # Store results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "repo_path": str(self.repo_path),
            "analyses": {},
            "recommendations": [],
            "actions_taken": [],
        }

        logger.info(f"Repository Overseer initialized for: {self.repo_path}")

    def _load_default_config(self) -> dict:
        """Load default configuration"""
        return {
            "code_analysis": {
                "enabled": True,
                "detect_refactoring": True,
                "detect_architecture": True,
                "detect_performance": True,
                "complexity_threshold": 10,
                "min_test_coverage": 80,
            },
            "documentation": {
                "enabled": True,
                "auto_generate_readme": True,
                "auto_generate_contributing": True,
                "generate_api_docs": True,
            },
            "dependency_management": {
                "enabled": True,
                "check_vulnerabilities": True,
                "auto_suggest_upgrades": True,
                "scan_frequency": "daily",
            },
            "cicd": {
                "enabled": True,
                "optimize_workflows": True,
                "suggest_tests": True,
                "suggest_linting": True,
                "suggest_deployment": True,
            },
            "issue_triaging": {
                "enabled": True,
                "auto_label": True,
                "auto_prioritize": True,
                "pattern_detection": True,
            },
            "automation": {
                "enabled": True,
                "code_formatting": True,
                "release_tagging": True,
                "environment_setup": True,
            },
            "monitoring": {
                "enabled": True,
                "continuous": True,
                "alert_on_issues": True,
                "performance_tracking": True,
            },
        }

    def analyze_code(self) -> dict[str, Any]:
        """
        Conduct deep code analysis.

        Returns:
            Dictionary containing analysis results
        """
        logger.info("Starting code analysis...")

        results = {
            "refactoring_opportunities": [],
            "architectural_improvements": [],
            "performance_optimizations": [],
            "complexity_issues": [],
        }

        if self.config["code_analysis"]["enabled"]:
            # Run code analysis
            analysis = self.code_analyzer.analyze()

            if self.config["code_analysis"]["detect_refactoring"]:
                results["refactoring_opportunities"] = analysis.get("refactoring", [])

            if self.config["code_analysis"]["detect_architecture"]:
                results["architectural_improvements"] = analysis.get("architecture", [])

            if self.config["code_analysis"]["detect_performance"]:
                results["performance_optimizations"] = analysis.get("performance", [])

            results["complexity_issues"] = analysis.get("complexity", [])
            results["code_quality_score"] = analysis.get("quality_score", 0)

        self.results["analyses"]["code"] = results
        logger.info(
            f"Code analysis complete. Found {len(results['refactoring_opportunities'])} refactoring opportunities"
        )

        return results

    def generate_documentation(self) -> dict[str, Any]:
        """
        Auto-generate and enhance documentation.

        Returns:
            Dictionary containing generated documentation info
        """
        logger.info("Generating documentation...")

        results = {
            "readme_updated": False,
            "contributing_generated": False,
            "api_docs_generated": False,
            "files_created": [],
        }

        if self.config["documentation"]["enabled"]:
            self.doc_generator.generate()

            if self.config["documentation"]["auto_generate_readme"]:
                readme_path = self.doc_generator.generate_readme()
                if readme_path:
                    results["readme_updated"] = True
                    results["files_created"].append(str(readme_path))

            if self.config["documentation"]["auto_generate_contributing"]:
                contrib_path = self.doc_generator.generate_contributing()
                if contrib_path:
                    results["contributing_generated"] = True
                    results["files_created"].append(str(contrib_path))

            if self.config["documentation"]["generate_api_docs"]:
                api_docs = self.doc_generator.generate_api_docs()
                results["api_docs_generated"] = len(api_docs) > 0
                results["files_created"].extend([str(p) for p in api_docs])

        self.results["analyses"]["documentation"] = results
        logger.info(
            f"Documentation generation complete. Created {len(results['files_created'])} files"
        )

        return results

    def manage_dependencies(self) -> dict[str, Any]:
        """
        Smart dependency management and security scanning.

        Returns:
            Dictionary containing dependency analysis and recommendations
        """
        logger.info("Analyzing dependencies...")

        results = {
            "outdated_packages": [],
            "vulnerable_packages": [],
            "upgrade_recommendations": [],
            "security_patches": [],
        }

        if self.config["dependency_management"]["enabled"]:
            deps = self.dependency_manager.analyze()

            results["outdated_packages"] = deps.get("outdated", [])

            if self.config["dependency_management"]["check_vulnerabilities"]:
                results["vulnerable_packages"] = deps.get("vulnerabilities", [])
                results["security_patches"] = deps.get("patches", [])

            if self.config["dependency_management"]["auto_suggest_upgrades"]:
                results["upgrade_recommendations"] = deps.get("recommendations", [])

        self.results["analyses"]["dependencies"] = results
        logger.info(
            f"Dependency analysis complete. Found {len(results['vulnerable_packages'])} vulnerabilities"
        )

        return results

    def optimize_cicd(self) -> dict[str, Any]:
        """
        Design and refine CI/CD workflows.

        Returns:
            Dictionary containing CI/CD optimization recommendations
        """
        logger.info("Optimizing CI/CD workflows...")

        results = {
            "workflow_optimizations": [],
            "test_improvements": [],
            "linting_suggestions": [],
            "deployment_recommendations": [],
        }

        if self.config["cicd"]["enabled"]:
            cicd = self.cicd_optimizer.analyze()

            if self.config["cicd"]["optimize_workflows"]:
                results["workflow_optimizations"] = cicd.get("optimizations", [])

            if self.config["cicd"]["suggest_tests"]:
                results["test_improvements"] = cicd.get("testing", [])

            if self.config["cicd"]["suggest_linting"]:
                results["linting_suggestions"] = cicd.get("linting", [])

            if self.config["cicd"]["suggest_deployment"]:
                results["deployment_recommendations"] = cicd.get("deployment", [])

        self.results["analyses"]["cicd"] = results
        logger.info(
            f"CI/CD optimization complete. Found {len(results['workflow_optimizations'])} improvements"
        )

        return results

    def triage_issues(self) -> dict[str, Any]:
        """
        Automate issue triaging, labeling, and prioritization.

        Returns:
            Dictionary containing issue triage results
        """
        logger.info("Triaging issues...")

        results = {
            "issues_processed": 0,
            "labels_applied": 0,
            "priorities_assigned": 0,
            "patterns_detected": [],
        }

        if self.config["issue_triaging"]["enabled"]:
            triage = self.issue_triager.process()

            results["issues_processed"] = triage.get("processed", 0)

            if self.config["issue_triaging"]["auto_label"]:
                results["labels_applied"] = triage.get("labeled", 0)

            if self.config["issue_triaging"]["auto_prioritize"]:
                results["priorities_assigned"] = triage.get("prioritized", 0)

            if self.config["issue_triaging"]["pattern_detection"]:
                results["patterns_detected"] = triage.get("patterns", [])

        self.results["analyses"]["issue_triage"] = results
        logger.info(
            f"Issue triage complete. Processed {results['issues_processed']} issues"
        )

        return results

    def generate_automation_scripts(self) -> dict[str, Any]:
        """
        Suggest intelligent automation scripts for repetitive tasks.

        Returns:
            Dictionary containing generated automation scripts
        """
        logger.info("Generating automation scripts...")

        results = {
            "scripts_generated": [],
            "formatting_scripts": [],
            "release_scripts": [],
            "setup_scripts": [],
        }

        if self.config["automation"]["enabled"]:
            automation = self.automation_engine.generate()

            if self.config["automation"]["code_formatting"]:
                results["formatting_scripts"] = automation.get("formatting", [])

            if self.config["automation"]["release_tagging"]:
                results["release_scripts"] = automation.get("release", [])

            if self.config["automation"]["environment_setup"]:
                results["setup_scripts"] = automation.get("setup", [])

            results["scripts_generated"] = (
                results["formatting_scripts"]
                + results["release_scripts"]
                + results["setup_scripts"]
            )

        self.results["analyses"]["automation"] = results
        logger.info(
            f"Automation generation complete. Created {len(results['scripts_generated'])} scripts"
        )

        return results

    def monitor_repository(self) -> dict[str, Any]:
        """
        Monitor repository activity and provide real-time recommendations.

        Returns:
            Dictionary containing monitoring results and recommendations
        """
        logger.info("Monitoring repository...")

        results = {
            "code_quality": {},
            "performance": {},
            "security": {},
            "collaboration": {},
            "recommendations": [],
        }

        if self.config["monitoring"]["enabled"]:
            monitoring = self.monitor.analyze()

            results["code_quality"] = monitoring.get("quality", {})
            results["performance"] = monitoring.get("performance", {})
            results["security"] = monitoring.get("security", {})
            results["collaboration"] = monitoring.get("collaboration", {})
            results["recommendations"] = monitoring.get("recommendations", [])

        self.results["analyses"]["monitoring"] = results
        logger.info(
            f"Monitoring complete. Generated {len(results['recommendations'])} recommendations"
        )

        return results

    def run_full_analysis(self) -> dict[str, Any]:
        """
        Execute all repository oversight tasks.

        Returns:
            Complete analysis results
        """
        logger.info("=" * 60)
        logger.info("Starting Full Repository Oversight Analysis")
        logger.info("=" * 60)

        # Run all analyses
        self.analyze_code()
        self.generate_documentation()
        self.manage_dependencies()
        self.optimize_cicd()
        self.triage_issues()
        self.generate_automation_scripts()
        self.monitor_repository()

        # Generate overall recommendations
        self._generate_recommendations()

        logger.info("=" * 60)
        logger.info("Repository Oversight Analysis Complete")
        logger.info("=" * 60)

        return self.results

    def _generate_recommendations(self):
        """Generate overall recommendations from all analyses"""
        recommendations = []

        # Code quality recommendations
        code_analysis = self.results["analyses"].get("code", {})
        if len(code_analysis.get("refactoring_opportunities", [])) > 5:
            recommendations.append(
                {
                    "category": "code_quality",
                    "priority": "high",
                    "message": f"Found {len(code_analysis['refactoring_opportunities'])} refactoring opportunities. Consider addressing high-priority items.",
                }
            )

        # Dependency recommendations
        deps = self.results["analyses"].get("dependencies", {})
        if len(deps.get("vulnerable_packages", [])) > 0:
            recommendations.append(
                {
                    "category": "security",
                    "priority": "critical",
                    "message": f"Found {len(deps['vulnerable_packages'])} vulnerable dependencies. Immediate action required.",
                }
            )

        # CI/CD recommendations
        cicd = self.results["analyses"].get("cicd", {})
        if len(cicd.get("workflow_optimizations", [])) > 0:
            recommendations.append(
                {
                    "category": "performance",
                    "priority": "medium",
                    "message": f"Found {len(cicd['workflow_optimizations'])} CI/CD optimization opportunities.",
                }
            )

        self.results["recommendations"] = recommendations

    def save_results(self, output_path: str | None = None):
        """
        Save analysis results to file.

        Args:
            output_path: Path to save results (default: repo_root/overseer-results.json)
        """
        if output_path is None:
            output_path = self.repo_path / "overseer-results.json"
        else:
            output_path = Path(output_path)

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"Results saved to: {output_path}")
        return output_path
