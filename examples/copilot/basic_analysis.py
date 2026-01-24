#!/usr/bin/env python3
"""
Example: Basic Repository Analysis with Elite Copilot

This example demonstrates how to:
1. Initialize the Elite Copilot
2. Run a basic repository analysis
3. View and interpret results
"""

import sys
from pathlib import Path

# Add the scripts directory to Python path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / '.github' / 'scripts'))

from elite_copilot import EliteCopilot, CopilotMode


def main():
    print("=" * 70)
    print("EXAMPLE: Basic Repository Analysis")
    print("=" * 70)
    print()
    
    # Initialize the Elite Copilot in assistant mode
    print("Step 1: Initializing Elite Copilot...")
    copilot = EliteCopilot()
    copilot.mode = CopilotMode.ASSISTANT
    print(f"✅ Copilot initialized in {copilot.mode.value} mode")
    print()
    
    # Run repository analysis
    print("Step 2: Running repository analysis...")
    repo_path = str(repo_root)
    results = copilot.analyze_repository(repo_path)
    print(f"✅ Analysis completed")
    print()
    
    # Display key results
    print("Step 3: Results Summary")
    print("-" * 70)
    print(f"📊 Health Score: {results['health_score']:.1f}/100")
    print(f"🔍 Insights Found: {len(results['insights'])}")
    print(f"💡 Recommendations: {len(results['recommendations'])}")
    print()
    
    # Show insights by category
    print("Step 4: Insights by Category")
    print("-" * 70)
    
    by_category = {}
    for insight in results['insights']:
        category = insight.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(insight)
    
    for category, insights in by_category.items():
        print(f"\n{category.upper()} ({len(insights)} insights):")
        for insight in insights:
            emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢',
                'info': 'ℹ️'
            }.get(insight.severity, '•')
            print(f"  {emoji} {insight.title}")
            print(f"     → {insight.suggested_action}")
    
    # Show recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Generate report
    print("\n" + "=" * 70)
    print("Step 5: Generating detailed report...")
    output_path = repo_root / 'EXAMPLE_ANALYSIS_REPORT.md'
    copilot.generate_report(results, str(output_path))
    print(f"✅ Report saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✨ Example completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the generated report")
    print("2. Try different modes (autopilot, guardian, mentor)")
    print("3. Customize the configuration")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
