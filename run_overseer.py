#!/usr/bin/env python3
"""
Repository Overseer CLI

Command-line interface for the repository overseer system.
"""

import argparse
import json
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from overseer import RepositoryOverseer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Advanced Full-Stack Repository Overseer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full analysis on current repository
  python run_overseer.py

  # Run full analysis on specific repository
  python run_overseer.py --repo /path/to/repo

  # Run only code analysis
  python run_overseer.py --only code

  # Save results to custom path
  python run_overseer.py --output results.json

  # Run with custom config
  python run_overseer.py --config custom_config.json
"""
    )
    
    parser.add_argument(
        '--repo',
        default='.',
        help='Path to repository (default: current directory)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to custom configuration file (JSON)'
    )
    
    parser.add_argument(
        '--output',
        help='Path to save results (default: overseer-results.json in repo root)'
    )
    
    parser.add_argument(
        '--only',
        choices=['code', 'docs', 'deps', 'cicd', 'issues', 'automation', 'monitor'],
        help='Run only specific analysis type'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load config
    config = None
    if args.config:
        try:
            with open(args.config) as f:
                config = json.load(f)
            logger.info(f"Loaded config from {args.config}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    # Initialize overseer
    try:
        overseer = RepositoryOverseer(args.repo, config)
    except Exception as e:
        logger.error(f"Error initializing overseer: {e}")
        sys.exit(1)
    
    # Run analysis
    try:
        if args.only:
            logger.info(f"Running {args.only} analysis only...")
            
            if args.only == 'code':
                results = {'code': overseer.analyze_code()}
            elif args.only == 'docs':
                results = {'docs': overseer.generate_documentation()}
            elif args.only == 'deps':
                results = {'deps': overseer.manage_dependencies()}
            elif args.only == 'cicd':
                results = {'cicd': overseer.optimize_cicd()}
            elif args.only == 'issues':
                results = {'issues': overseer.triage_issues()}
            elif args.only == 'automation':
                results = {'automation': overseer.generate_automation_scripts()}
            elif args.only == 'monitor':
                results = {'monitor': overseer.monitor_repository()}
        else:
            logger.info("Running full repository analysis...")
            results = overseer.run_full_analysis()
        
        # Save results
        output_path = overseer.save_results(args.output)
        
        # Print summary
        print("\n" + "=" * 60)
        print("REPOSITORY OVERSEER ANALYSIS COMPLETE")
        print("=" * 60)
        
        if 'analyses' in results:
            print("\n📊 Analysis Summary:")
            
            if 'code' in results['analyses']:
                code = results['analyses']['code']
                print(f"\n  Code Quality:")
                print(f"    - Quality Score: {code.get('quality_score', 0)}/100")
                print(f"    - Refactoring Opportunities: {len(code.get('refactoring_opportunities', []))}")
                print(f"    - Architectural Improvements: {len(code.get('architectural_improvements', []))}")
                print(f"    - Performance Issues: {len(code.get('performance_optimizations', []))}")
            
            if 'dependencies' in results['analyses']:
                deps = results['analyses']['dependencies']
                print(f"\n  Dependencies:")
                print(f"    - Vulnerable Packages: {len(deps.get('vulnerable_packages', []))}")
                print(f"    - Outdated Packages: {len(deps.get('outdated_packages', []))}")
                print(f"    - Upgrade Recommendations: {len(deps.get('upgrade_recommendations', []))}")
            
            if 'cicd' in results['analyses']:
                cicd = results['analyses']['cicd']
                print(f"\n  CI/CD:")
                print(f"    - Workflow Optimizations: {len(cicd.get('workflow_optimizations', []))}")
                print(f"    - Test Improvements: {len(cicd.get('test_improvements', []))}")
            
            if 'monitoring' in results['analyses']:
                monitor = results['analyses']['monitoring']
                recs = monitor.get('recommendations', [])
                print(f"\n  Monitoring:")
                print(f"    - Total Recommendations: {len(recs)}")
                
                # Group by priority
                high = sum(1 for r in recs if r.get('priority') == 'high')
                medium = sum(1 for r in recs if r.get('priority') == 'medium')
                low = sum(1 for r in recs if r.get('priority') == 'low')
                
                print(f"    - High Priority: {high}")
                print(f"    - Medium Priority: {medium}")
                print(f"    - Low Priority: {low}")
        
        print(f"\n📁 Detailed results saved to: {output_path}")
        print("\n" + "=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
