#!/usr/bin/env python
"""
Direct installation script that runs everything in sequence.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_step(step_num, name, command):
    """Run a single step and report results."""
    print("\n" + "=" * 70)
    print(f"STEP {step_num}: {name}")
    print("=" * 70)
    print(f"Command: {command}\n")

    try:
        if isinstance(command, str):
            # If it's a string, use shell=True
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            # If it's a list, use it as argv
            result = subprocess.run(command, capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"\n✓ STEP {step_num} PASSED")
            return True
        else:
            print(f"\n✗ STEP {step_num} FAILED (exit code: {result.returncode})")
            return False
    except Exception as e:
        print(f"✗ STEP {step_num} ERROR: {e}")
        return False


def main():
    """Run the complete installation."""
    os.chdir(r"C:\Users\aw789\autonomous-github-agent")

    print("\n" + "=" * 70)
    print("AUTONOMOUS GITHUB AGENT - COMPLETE INSTALLATION")
    print("=" * 70)
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")

    steps = [
        (1, "Create directories and init files", f"{sys.executable} quick_setup.py"),
        (2, "Create core modules", f"{sys.executable} create_core_files.py"),
        (3, "Create agent modules", f"{sys.executable} create_agents.py"),
        (4, "Create CLI and tests", f"{sys.executable} create_cli.py"),
        (
            5,
            "Install package (pip install -e .)",
            f"{sys.executable} -m pip install -e .",
        ),
    ]

    results = {}

    for step_num, name, command in steps:
        success = run_step(step_num, name, command)
        results[f"Step {step_num}: {name}"] = success
        if not success:
            print(f"\nContinuing with next step despite failure...")

    # Run verification
    print("\n" + "=" * 70)
    print("VERIFICATION: Running verify_installation.py")
    print("=" * 70 + "\n")
    verify_success = run_step(
        6, "Verify installation", f"{sys.executable} verify_installation.py"
    )
    results["Step 6: Verify installation"] = verify_success

    # Summary
    print("\n\n" + "=" * 70)
    print("INSTALLATION SUMMARY")
    print("=" * 70)
    for step, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{step}: {status}")

    all_success = all(results.values())

    print("\n" + "=" * 70)
    if all_success:
        print("✓ ALL STEPS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nThe Autonomous GitHub Agent is ready to use!")
        print("Next steps:")
        print("1. Edit the .env file and add your GitHub token and LLM credentials")
        print("2. Run: python -m autonomous_agent.cli.main --help")
        return 0
    else:
        print("⚠ SOME STEPS FAILED - CHECK OUTPUT ABOVE")
        print("=" * 70)
        failed_steps = [step for step, success in results.items() if not success]
        print("\nFailed steps:")
        for step in failed_steps:
            print(f"  - {step}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
