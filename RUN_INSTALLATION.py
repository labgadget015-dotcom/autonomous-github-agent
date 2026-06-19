#!/usr/bin/env python3
"""
DIRECT EXECUTION INSTALLER - Workaround for PowerShell issues
Executes all installation steps directly without subprocess
"""
import sys
import os
from pathlib import Path
import subprocess

def main():
    # Change to the installation directory
    install_dir = Path(r"C:\Users\aw789\autonomous-github-agent")
    os.chdir(install_dir)
    sys.path.insert(0, str(install_dir))
    
    print("\n" + "="*70)
    print("AUTONOMOUS GITHUB AGENT - DIRECT EXECUTION INSTALLER")
    print("="*70)
    print(f"\nPython: {sys.executable}")
    print(f"Version: {sys.version}")
    print(f"Directory: {os.getcwd()}\n")
    
    results = {}
    
    # Step 1: quick_setup
    print("\n" + "-"*70)
    print("STEP 1: Creating directory structure and init files")
    print("-"*70)
    try:
        import quick_setup
        quick_setup.main()
        results["Step 1: Directory structure"] = True
        print("✅ SUCCESS")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results["Step 1: Directory structure"] = False
    
    # Step 2: create_core_files
    print("\n" + "-"*70)
    print("STEP 2: Creating core modules")
    print("-"*70)
    try:
        # Clear cache
        if 'create_core_files' in sys.modules:
            del sys.modules['create_core_files']
        import create_core_files
        create_core_files.main()
        results["Step 2: Core modules"] = True
        print("✅ SUCCESS")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results["Step 2: Core modules"] = False
    
    # Step 3: create_agents
    print("\n" + "-"*70)
    print("STEP 3: Creating agent modules")
    print("-"*70)
    try:
        if 'create_agents' in sys.modules:
            del sys.modules['create_agents']
        import create_agents
        create_agents.main()
        results["Step 3: Agent modules"] = True
        print("✅ SUCCESS")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results["Step 3: Agent modules"] = False
    
    # Step 4: create_cli
    print("\n" + "-"*70)
    print("STEP 4: Creating CLI and tests")
    print("-"*70)
    try:
        if 'create_cli' in sys.modules:
            del sys.modules['create_cli']
        import create_cli
        create_cli.main()
        results["Step 4: CLI and tests"] = True
        print("✅ SUCCESS")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results["Step 4: CLI and tests"] = False
    
    # Step 5: pip install
    print("\n" + "-"*70)
    print("STEP 5: Installing package with pip")
    print("-"*70)
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
        print(f"Running: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, cwd=str(install_dir))
        if result.returncode == 0:
            results["Step 5: Pip install"] = True
            print("✅ SUCCESS")
        else:
            results["Step 5: Pip install"] = False
            print("❌ FAILED")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results["Step 5: Pip install"] = False
    
    # Step 6: verify
    print("\n" + "-"*70)
    print("STEP 6: Verifying installation")
    print("-"*70)
    try:
        if 'verify_installation' in sys.modules:
            del sys.modules['verify_installation']
        import verify_installation
        success = verify_installation.verify_installation()
        results["Step 6: Verification"] = success
        if success:
            print("✅ SUCCESS")
        else:
            print("⚠️ Check details above")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results["Step 6: Verification"] = False
    
    # Summary
    print("\n" + "="*70)
    print("INSTALLATION SUMMARY")
    print("="*70)
    for step, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{step}: {status}")
    
    # Overall status
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nNext steps:")
        print("1. Edit .env file with your GitHub token and LLM credentials")
        print("2. Run: autonomous-agent --help")
        print("3. Run: autonomous-agent health-check --repo owner/repo")
    else:
        print("⚠️ SOME STEPS FAILED")
        print("="*70)
        print("\nFailed steps:")
        for step, success in results.items():
            if not success:
                print(f"  - {step}")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
