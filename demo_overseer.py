#!/usr/bin/env python3
"""
Repository Overseer Demo

This script demonstrates the capabilities of the repository overseer system
by running a full analysis and showcasing the results.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from overseer import RepositoryOverseer


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_code_analysis(overseer: RepositoryOverseer):
    """Demonstrate code analysis capabilities"""
    print_section("1. CODE ANALYSIS")

    results = overseer.analyze_code()

    print("\n📊 Code Quality Metrics:")
    print(f"   • Quality Score: {results.get('code_quality_score', 0)}/100")
    print(f"   • Files Analyzed: {len(list(overseer.repo_path.glob('**/*.py')))}")

    print("\n🔍 Issues Found:")
    print(
        f"   • Refactoring Opportunities: {len(results['refactoring_opportunities'])}"
    )
    print(f"   • Architectural Issues: {len(results['architectural_improvements'])}")
    print(f"   • Performance Problems: {len(results['performance_optimizations'])}")

    # Show top 3 refactoring opportunities
    if results["refactoring_opportunities"]:
        print("\n📝 Top Refactoring Opportunities:")
        for i, issue in enumerate(results["refactoring_opportunities"][:3], 1):
            print(f"   {i}. {issue['type']}: {issue.get('recommendation', 'N/A')}")


def demo_documentation(overseer: RepositoryOverseer):
    """Demonstrate documentation generation"""
    print_section("2. DOCUMENTATION GENERATION")

    results = overseer.generate_documentation()

    print("\n📚 Documentation Created:")
    print(f"   • README Enhanced: {results['readme_updated']}")
    print(f"   • CONTRIBUTING Guide: {results['contributing_generated']}")
    print(f"   • API Docs: {results['api_docs_generated']}")
    print(f"   • Total Files: {len(results['files_created'])}")

    if results["files_created"]:
        print("\n📄 Generated Files:")
        for file in results["files_created"][:5]:
            print(f"   • {file}")


def demo_dependencies(overseer: RepositoryOverseer):
    """Demonstrate dependency management"""
    print_section("3. DEPENDENCY MANAGEMENT")

    results = overseer.manage_dependencies()

    print("\n📦 Dependency Analysis:")
    print(f"   • Outdated Packages: {len(results['outdated_packages'])}")
    print(f"   • Vulnerable Packages: {len(results['vulnerable_packages'])}")
    print(f"   • Recommendations: {len(results['upgrade_recommendations'])}")

    if results["vulnerable_packages"]:
        print("\n⚠️  Security Vulnerabilities:")
        for vuln in results["vulnerable_packages"][:3]:
            print(f"   • {vuln['package']}: {vuln['description']}")


def demo_cicd(overseer: RepositoryOverseer):
    """Demonstrate CI/CD optimization"""
    print_section("4. CI/CD WORKFLOW OPTIMIZATION")

    results = overseer.optimize_cicd()

    print("\n⚙️  Workflow Analysis:")
    print(f"   • Optimization Opportunities: {len(results['workflow_optimizations'])}")
    print(f"   • Test Improvements: {len(results['test_improvements'])}")
    print(f"   • Linting Suggestions: {len(results['linting_suggestions'])}")
    print(
        f"   • Deployment Recommendations: {len(results['deployment_recommendations'])}"
    )

    if results["workflow_optimizations"]:
        print("\n💡 Top Optimizations:")
        for i, opt in enumerate(results["workflow_optimizations"][:3], 1):
            print(f"   {i}. {opt.get('recommendation', 'N/A')}")


def demo_issues(overseer: RepositoryOverseer):
    """Demonstrate issue triaging"""
    print_section("5. ISSUE TRIAGING")

    results = overseer.triage_issues()

    print("\n🏷️  Triaging Capabilities:")
    print(f"   • Issues Processed: {results['issues_processed']}")
    print(f"   • Labels Applied: {results['labels_applied']}")
    print(f"   • Priorities Assigned: {results['priorities_assigned']}")
    print(f"   • Patterns Detected: {len(results['patterns_detected'])}")

    # Demo: Analyze sample issues
    print("\n📋 Example Issue Analysis:")

    sample_issues = [
        (
            "Critical bug in authentication",
            "The login feature is broken and causing security issues",
        ),
        ("Add dark mode feature", "Would be nice to have a dark theme option"),
        ("Documentation outdated", "The README needs to be updated with new features"),
    ]

    triager = overseer.issue_triager
    for title, body in sample_issues:
        result = triager.analyze_issue_content(title, body)
        print(f"\n   Issue: '{title}'")
        print(f"   → Labels: {', '.join(result['labels'])}")
        print(f"   → Priority: {result['priority']}")


def demo_automation(overseer: RepositoryOverseer):
    """Demonstrate automation script generation"""
    print_section("6. AUTOMATION SCRIPTS")

    results = overseer.generate_automation_scripts()

    print("\n🤖 Scripts Generated:")
    print(f"   • Formatting Scripts: {len(results['formatting_scripts'])}")
    print(f"   • Release Scripts: {len(results['release_scripts'])}")
    print(f"   • Setup Scripts: {len(results['setup_scripts'])}")
    print(f"   • Total Scripts: {len(results['scripts_generated'])}")

    if results["scripts_generated"]:
        print("\n📜 Created Scripts:")
        for script in results["scripts_generated"]:
            print(f"   • {script}")


def demo_monitoring(overseer: RepositoryOverseer):
    """Demonstrate repository monitoring"""
    print_section("7. REPOSITORY MONITORING")

    results = overseer.monitor_repository()

    print("\n📊 Health Metrics:")

    quality = results.get("code_quality", {})
    print(f"\n   Code Quality:")
    print(f"   • Test Coverage: {quality.get('test_coverage', 0)}%")
    print(f"   • Has Linting: {quality.get('has_linting', False)}")
    print(f"   • Documentation Coverage: {quality.get('documentation_coverage', 0)}%")

    security = results.get("security", {})
    print(f"\n   Security:")
    print(f"   • Security Policy: {security.get('has_security_policy', False)}")
    print(f"   • Dependabot: {security.get('has_dependabot', False)}")
    print(f"   • Security Workflows: {len(security.get('security_workflows', []))}")

    collab = results.get("collaboration", {})
    print(f"\n   Collaboration:")
    print(f"   • Contributing Guide: {collab.get('has_contributing_guide', False)}")
    print(f"   • Code of Conduct: {collab.get('has_code_of_conduct', False)}")
    print(f"   • Issue Templates: {collab.get('has_issue_templates', False)}")

    recommendations = results.get("recommendations", [])
    print(f"\n💡 Total Recommendations: {len(recommendations)}")

    if recommendations:
        print("\n🎯 Top Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")


def main():
    """Run the demo"""
    print("\n" + "🎯" * 35)
    print("          REPOSITORY OVERSEER DEMONSTRATION")
    print("🎯" * 35)

    print("\n📂 Initializing overseer for current repository...")

    # Initialize overseer
    overseer = RepositoryOverseer(".")

    print("✅ Overseer initialized successfully!")

    # Run demonstrations
    try:
        demo_code_analysis(overseer)
        demo_documentation(overseer)
        demo_dependencies(overseer)
        demo_cicd(overseer)
        demo_issues(overseer)
        demo_automation(overseer)
        demo_monitoring(overseer)

        print_section("DEMO COMPLETE")
        print("\n✨ The Repository Overseer has demonstrated all 7 capabilities!")
        print("\n📝 To run your own analysis, use:")
        print("   python run_overseer.py")
        print("\n📚 For more information, see README.md")
        print()

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
