"""
Post-installation verification script.
Run this AFTER completing the installation to verify everything works.
"""

import sys
from pathlib import Path

def check_mark(condition):
    return "✅" if condition else "❌"

def verify_installation():
    """Verify the autonomous-github-agent installation."""
    print("\n" + "="*60)
    print("  AUTONOMOUS GITHUB AGENT - INSTALLATION VERIFICATION")
    print("="*60 + "\n")
    
    results = {}
    
    # Check 1: Python version
    print("Checking Python version...")
    py_version = sys.version_info
    results['python'] = py_version >= (3, 11)
    print(f"{check_mark(results['python'])} Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Check 2: Package can be imported
    print("\nChecking package import...")
    try:
        import autonomous_agent
        results['import'] = True
        print(f"✅ Package imported successfully")
        print(f"   Version: {autonomous_agent.__version__}")
    except ImportError as e:
        results['import'] = False
        print(f"❌ Failed to import package: {e}")
    
    # Check 3: Core modules exist
    if results['import']:
        print("\nChecking core modules...")
        core_modules = [
            'autonomous_agent.core.orchestrator',
            'autonomous_agent.core.github_client',
            'autonomous_agent.core.config',
        ]
        
        core_ok = True
        for module in core_modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except Exception as e:
                print(f"  ❌ {module}: {e}")
                core_ok = False
        results['core_modules'] = core_ok
    
    # Check 4: Agents exist
    if results['import']:
        print("\nChecking agent modules...")
        agent_modules = [
            'autonomous_agent.agents.issue_analyzer',
            'autonomous_agent.agents.pr_reviewer',
            'autonomous_agent.agents.code_quality',
        ]
        
        agents_ok = True
        for module in agent_modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except Exception as e:
                print(f"  ❌ {module}: {e}")
                agents_ok = False
        results['agents'] = agents_ok
    
    # Check 5: Directory structure
    print("\nChecking directory structure...")
    base_dir = Path(__file__).parent
    required_dirs = [
        'autonomous_agent',
        'autonomous_agent/core',
        'autonomous_agent/agents',
        'autonomous_agent/utils',
        'tests',
        'config',
        'logs',
    ]
    
    dirs_ok = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        exists = full_path.exists()
        print(f"  {check_mark(exists)} {dir_path}")
        if not exists:
            dirs_ok = False
    results['directories'] = dirs_ok
    
    # Check 6: .env file
    print("\nChecking .env file...")
    env_file = base_dir / ".env"
    results['env_file'] = env_file.exists()
    print(f"{check_mark(results['env_file'])} .env file exists")
    
    if results['env_file']:
        # Check if tokens are configured
        env_content = env_file.read_text()
        has_github_token = 'GITHUB_TOKEN=' in env_content and 'ghp_your' not in env_content
        has_llm_key = ('OPENAI_API_KEY=' in env_content and 'sk-your' not in env_content) or \
                      ('ANTHROPIC_API_KEY=' in env_content and 'sk-ant-your' not in env_content)
        
        print(f"\n  Configuration status:")
        print(f"  {check_mark(has_github_token)} GITHUB_TOKEN configured")
        print(f"  {check_mark(has_llm_key)} LLM API key configured")
        
        results['env_configured'] = has_github_token and has_llm_key
    else:
        print("  ⚠️  Please create .env file from .env.example")
        results['env_configured'] = False
    
    # Check 7: CLI availability
    print("\nChecking CLI availability...")
    import subprocess
    try:
        result = subprocess.run(
            ['autonomous-agent', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        results['cli'] = result.returncode == 0
        print(f"{check_mark(results['cli'])} CLI command 'autonomous-agent' available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        results['cli'] = False
        print(f"❌ CLI command 'autonomous-agent' not available")
        print(f"   Try: pip install -e . --force-reinstall")
    
    # Summary
    print("\n" + "="*60)
    print("  VERIFICATION SUMMARY")
    print("="*60 + "\n")
    
    all_critical_passed = (
        results.get('python', False) and
        results.get('import', False) and
        results.get('core_modules', False) and
        results.get('directories', False)
    )
    
    if all_critical_passed:
        print("✅ Core installation: SUCCESS")
    else:
        print("❌ Core installation: FAILED")
        print("\n   Please re-run: python install.py")
    
    if results.get('env_configured', False):
        print("✅ Configuration: COMPLETE")
    else:
        print("⚠️  Configuration: INCOMPLETE")
        print("\n   Please edit .env and add:")
        print("   - GITHUB_TOKEN=your_token_here")
        print("   - OPENAI_API_KEY=your_key_here (or ANTHROPIC_API_KEY)")
    
    if results.get('cli', False):
        print("✅ CLI: READY")
    else:
        print("⚠️  CLI: NOT AVAILABLE")
        print("\n   Try: pip install -e . --force-reinstall")
    
    # Overall status
    print("\n" + "="*60)
    if all_critical_passed and results.get('env_configured') and results.get('cli'):
        print("  🎉 INSTALLATION COMPLETE AND VERIFIED!")
        print("="*60 + "\n")
        print("Next steps:")
        print("  1. Try: autonomous-agent list-agents")
        print("  2. Try: autonomous-agent config-check")
        print("  3. Try: autonomous-agent health-check --repo owner/repo")
        print("\n  Happy automating! 🚀")
    elif all_critical_passed:
        print("  ⚠️  INSTALLATION MOSTLY COMPLETE")
        print("="*60 + "\n")
        print("Next steps:")
        if not results.get('env_configured'):
            print("  1. Edit .env file with your API tokens")
        if not results.get('cli'):
            print("  2. Run: pip install -e . --force-reinstall")
        print("\n  Then verify again: python verify_installation.py")
    else:
        print("  ❌ INSTALLATION INCOMPLETE")
        print("="*60 + "\n")
        print("Please re-run: python install.py")
    
    print()
    return all_critical_passed

if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)
