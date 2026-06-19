#!/usr/bin/env python
"""
Test if we can execute Python at all in this environment
"""
import sys
import os
from pathlib import Path

print("=" * 70)
print("ENVIRONMENT TEST")
print("=" * 70)

print(f"\nPython Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Current Directory: {os.getcwd()}")

# Try to navigate
target = Path(r"C:\Users\aw789\autonomous-github-agent")
print(f"\nTarget Directory: {target}")
print(f"Exists: {target.exists()}")

if target.exists():
    os.chdir(target)
    print(f"Changed to: {os.getcwd()}")
    
    print("\nFiles in directory:")
    files = sorted([f.name for f in target.glob("*.py")])
    for f in files[:10]:
        print(f"  - {f}")
    
    # Try to import quick_setup
    print("\nTrying to import quick_setup...")
    try:
        sys.path.insert(0, str(target))
        import quick_setup
        print("✅ Successfully imported quick_setup module")
        print(f"   Has main: {hasattr(quick_setup, 'main')}")
    except Exception as e:
        print(f"❌ Failed to import: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ Directory does not exist!")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
