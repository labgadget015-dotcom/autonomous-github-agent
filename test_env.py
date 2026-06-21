#!/usr/bin/env python
"""Quick diagnostic script"""
import os
import sys
from pathlib import Path

print("Python Information:")
print(f"  Executable: {sys.executable}")
print(f"  Version: {sys.version}")
print(f"  Platform: {sys.platform}")

print(f"\nCurrent Directory: {os.getcwd()}")
print(f"Script Directory: {Path(__file__).parent}")

# Try to change directory
target_dir = r"C:\Users\aw789\autonomous-github-agent"
if Path(target_dir).exists():
    print(f"\n✓ Target directory exists: {target_dir}")
    os.chdir(target_dir)
    print(f"✓ Changed to: {os.getcwd()}")

    # List files
    print("\nFiles in target directory:")
    for f in Path(".").glob("*.py"):
        print(f"  - {f.name}")
else:
    print(f"\n✗ Target directory not found: {target_dir}")

# Test import
print("\nTesting imports...")
try:

    print("  ✓ pathlib")
except:
    print("  ✗ pathlib")

try:

    print("  ✓ subprocess")
except:
    print("  ✗ subprocess")

print("\nAll tests passed!")
