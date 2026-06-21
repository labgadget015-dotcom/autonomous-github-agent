"""
Wrapper script to execute install.py programmatically.
This script imports and runs install.py directly.
"""

import sys
from pathlib import Path

# Add the autonomous-github-agent directory to path
agent_dir = Path(r"C:\Users\aw789\autonomous-github-agent")
sys.path.insert(0, str(agent_dir))

# Change to the directory
import os

os.chdir(agent_dir)

# Import and run the install module
try:
    import install

    install.main()
except Exception as e:
    print(f"Error running installation: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
