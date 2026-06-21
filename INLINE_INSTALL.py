#!/usr/bin/env python3
"""Inline execution of installation steps"""
import os
import sys

# Set up paths
os.chdir(r"C:\Users\aw789\autonomous-github-agent")
sys.path.insert(0, r"C:\Users\aw789\autonomous-github-agent")

print("\n" + "=" * 70)
print("  AUTONOMOUS GITHUB AGENT - INLINE INSTALLATION")
print("=" * 70)

# Execute each step inline
print("\nSTEP 1: Running quick_setup.py...")
try:
    exec(open("quick_setup.py").read())
    print("✅ Step 1 complete")
except Exception as e:
    print(f"❌ Step 1 failed: {e}")

print("\nSTEP 2: Running create_core_files.py...")
try:
    exec(open("create_core_files.py").read())
    print("✅ Step 2 complete")
except Exception as e:
    print(f"❌ Step 2 failed: {e}")

print("\nSTEP 3: Running create_agents.py...")
try:
    exec(open("create_agents.py").read())
    print("✅ Step 3 complete")
except Exception as e:
    print(f"❌ Step 3 failed: {e}")

print("\nSTEP 4: Running create_cli.py...")
try:
    exec(open("create_cli.py").read())
    print("✅ Step 4 complete")
except Exception as e:
    print(f"❌ Step 4 failed: {e}")

print("\nSTEP 5: Installing with pip...")
import subprocess

try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        capture_output=True,
        text=True,
        cwd=r"C:\Users\aw789\autonomous-github-agent",
    )
    if result.returncode == 0:
        print("✅ Step 5 complete")
    else:
        print(f"❌ Step 5 failed: {result.stderr}")
except Exception as e:
    print(f"❌ Step 5 failed: {e}")

print("\nSTEP 6: Running verify_installation.py...")
try:
    exec(open("verify_installation.py").read())
    print("✅ Step 6 complete")
except Exception as e:
    print(f"❌ Step 6 failed: {e}")

print("\n" + "=" * 70)
print("  INSTALLATION SEQUENCE COMPLETE")
print("=" * 70 + "\n")
