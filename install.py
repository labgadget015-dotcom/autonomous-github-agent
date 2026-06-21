"""
Master installation script - Run this to set up everything!
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(r"C:\Users\aw789\autonomous-github-agent")


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def run_script(script_name):
    """Run a Python script."""
    script_path = BASE_DIR / script_name
    if not script_path.exists():
        print(f"❌ {script_name} not found!")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Error running {script_name}:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Exception running {script_name}: {e}")
        return False


def main():
    """Main installation routine."""
    print_header("Autonomous GitHub Agent - Complete Setup")

    print("This script will set up the entire framework in the following steps:")
    print("  1. Create directory structure")
    print("  2. Create core modules")
    print("  3. Create specialized agents")
    print("  4. Create CLI and tests")
    print("  5. Install dependencies")
    print("  6. Create .env file\n")

    input("Press Enter to continue...")

    # Step 1: Directory setup
    print_header("Step 1/6: Creating Directory Structure")
    if run_script("quick_setup.py"):
        print("✅ Directory structure created")
    else:
        print("⚠️  Could not run quick_setup.py - directories may already exist")

    # Step 2: Core modules
    print_header("Step 2/6: Creating Core Modules")
    if run_script("create_core_files.py"):
        print("✅ Core modules created")
    else:
        print("❌ Failed to create core modules")
        return

    # Step 3: Agents
    print_header("Step 3/6: Creating Specialized Agents")
    if run_script("create_agents.py"):
        print("✅ All agents created")
    else:
        print("❌ Failed to create agents")
        return

    # Step 4: CLI and tests
    print_header("Step 4/6: Creating CLI and Tests")
    if run_script("create_cli.py"):
        print("✅ CLI and tests created")
    else:
        print("❌ Failed to create CLI")
        return

    # Step 5: Install dependencies
    print_header("Step 5/6: Installing Dependencies")
    print("Installing package in development mode...\n")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print("⚠️  Installation had issues:")
            print(result.stderr)
            print("\nYou may need to run manually: pip install -e .")
    except Exception as e:
        print(f"⚠️  Could not install automatically: {e}")
        print("Please run manually: pip install -e .")

    # Step 6: Create .env
    print_header("Step 6/6: Creating Configuration File")

    env_path = BASE_DIR / ".env"
    env_example_path = BASE_DIR / ".env.example"

    if not env_path.exists() and env_example_path.exists():
        import shutil

        shutil.copy(env_example_path, env_path)
        print("✅ Created .env file from template")
        print("\n⚠️  IMPORTANT: Edit .env and add your tokens:")
        print("  - GITHUB_TOKEN=your_token_here")
        print("  - OPENAI_API_KEY=your_key_here (or ANTHROPIC_API_KEY)")
    elif env_path.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  Could not create .env file")

    # Final summary
    print_header("🎉 Setup Complete!")

    print("Your Autonomous GitHub Agent framework is ready!\n")
    print("Next steps:\n")
    print("1. Edit .env file with your API tokens")
    print("2. Verify setup: autonomous-agent config-check")
    print("3. List agents: autonomous-agent list-agents")
    print("4. Try it: autonomous-agent health-check --repo owner/repo\n")
    print("For full documentation, see INSTALL.md and README.md\n")
    print("=" * 60)


if __name__ == "__main__":
    main()
