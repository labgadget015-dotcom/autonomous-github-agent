"""
Master installation script for Autonomous GitHub Agent.
Runs all installation steps in sequence.
"""

import os
import sys
import subprocess
from pathlib import Path

# Change to the script directory
os.chdir(Path(__file__).parent)


def run_script(script_name, description):
    """Run a Python script and report status."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            [sys.executable, script_name], check=True, capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False


def run_pip_install():
    """Run pip install."""
    print(f"\n{'='*60}")
    print(f"  Installing package with pip install -e .")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print("✓ Package installation - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Package installation - FAILED")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ Package installation - ERROR: {e}")
        return False


def create_env_file():
    """Create .env file from .env.example."""
    print(f"\n{'='*60}")
    print(f"  Creating .env file from .env.example")
    print(f"{'='*60}\n")

    env_example = Path(".env.example")
    env_file = Path(".env")

    if not env_example.exists():
        print("✗ .env.example not found")
        return False

    if env_file.exists():
        print("ℹ .env file already exists, skipping...")
        return True

    try:
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
        print("✓ Created .env file")
        return True
    except Exception as e:
        print(f"✗ Failed to create .env file: {e}")
        return False


def verify_installation():
    """Verify the installation."""
    print(f"\n{'='*60}")
    print(f"  Verifying Installation")
    print(f"{'='*60}\n")

    print(f"Python version: {sys.version}")

    try:
        import autonomous_agent

        print(f"✓ Package imported successfully")
        print(f"  Version: {autonomous_agent.__version__}")
        return True
    except Exception as e:
        print(f"✗ Failed to import package: {e}")
        return False


def main():
    """Run all installation steps."""
    print("\n" + "=" * 60)
    print("  AUTONOMOUS GITHUB AGENT - MASTER INSTALLATION")
    print("=" * 60)

    steps = [
        ("quick_setup.py", "Step 1/7: Creating directory structure"),
        ("create_core_files.py", "Step 2/7: Creating core modules"),
        ("create_agents.py", "Step 3/7: Creating agent modules"),
        ("create_cli.py", "Step 4/7: Creating CLI and tests"),
    ]

    results = {}

    # Run Python scripts
    for script, description in steps:
        results[description] = run_script(script, description)

    # Run pip install
    results["Step 5/7: Package installation"] = run_pip_install()

    # Create .env file
    results["Step 6/7: Create .env file"] = create_env_file()

    # Verify installation
    results["Step 7/7: Verify installation"] = verify_installation()

    # Summary
    print("\n" + "=" * 60)
    print("  INSTALLATION SUMMARY")
    print("=" * 60 + "\n")

    for step, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{step}: {status}")

    all_success = all(results.values())

    print("\n" + "=" * 60)
    if all_success:
        print("  ✓ ALL STEPS COMPLETED SUCCESSFULLY!")
    else:
        print("  ⚠ SOME STEPS FAILED - CHECK OUTPUT ABOVE")
    print("=" * 60 + "\n")

    if not all_success:
        print("Steps that need manual intervention:")
        for step, success in results.items():
            if not success:
                print(f"  - {step}")
        print()

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
