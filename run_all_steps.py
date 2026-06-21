#!/usr/bin/env python
"""
Run all installation steps directly.
"""
import os
import sys
from pathlib import Path

# Change to the directory
os.chdir(Path(__file__).parent)

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("  AUTONOMOUS GITHUB AGENT - INSTALLATION SEQUENCE")
print("=" * 70)

results = {}

# Step 1: quick_setup.py
print("\nStep 1/5: Running quick_setup.py...")
print("-" * 70)
try:
    import quick_setup

    quick_setup.main()
    results["Step 1: quick_setup.py"] = "SUCCESS"
except Exception as e:
    print(f"ERROR: {e}")
    results["Step 1: quick_setup.py"] = f"FAILED - {e}"

# Step 2: create_core_files.py
print("\n\nStep 2/5: Running create_core_files.py...")
print("-" * 70)
try:
    # Reload to get fresh module

    if "create_core_files" in sys.modules:
        del sys.modules["create_core_files"]
    import create_core_files

    create_core_files.main()
    results["Step 2: create_core_files.py"] = "SUCCESS"
except Exception as e:
    print(f"ERROR: {e}")
    results["Step 2: create_core_files.py"] = f"FAILED - {e}"

# Step 3: create_agents.py
print("\n\nStep 3/5: Running create_agents.py...")
print("-" * 70)
try:
    if "create_agents" in sys.modules:
        del sys.modules["create_agents"]
    import create_agents

    create_agents.main()
    results["Step 3: create_agents.py"] = "SUCCESS"
except Exception as e:
    print(f"ERROR: {e}")
    results["Step 3: create_agents.py"] = f"FAILED - {e}"

# Step 4: create_cli.py
print("\n\nStep 4/5: Running create_cli.py...")
print("-" * 70)
try:
    if "create_cli" in sys.modules:
        del sys.modules["create_cli"]
    import create_cli

    create_cli.main()
    results["Step 4: create_cli.py"] = "SUCCESS"
except Exception as e:
    print(f"ERROR: {e}")
    results["Step 4: create_cli.py"] = f"FAILED - {e}"

# Step 5: pip install -e .
print("\n\nStep 5/5: Running pip install -e ...")
print("-" * 70)
try:
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    results["Step 5: pip install -e ."] = "SUCCESS"
except Exception as e:
    print(f"ERROR: {e}")
    results["Step 5: pip install -e ."] = f"FAILED - {e}"

# Summary
print("\n\n" + "=" * 70)
print("  INSTALLATION SUMMARY")
print("=" * 70)
for step, status in results.items():
    print(f"  {step}: {status}")

print("\n" + "=" * 70)
print("  Running verify_installation.py...")
print("=" * 70)
try:
    if "verify_installation" in sys.modules:
        del sys.modules["verify_installation"]
    import verify_installation

    verify_installation.main()
except Exception as e:
    print(f"ERROR: {e}")
