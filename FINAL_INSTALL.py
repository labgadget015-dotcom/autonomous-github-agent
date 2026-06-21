#!/usr/bin/env python3
"""
COMPREHENSIVE INSTALLATION ORCHESTRATOR
Executes autonomous-github-agent setup in correct sequence.
Handles all steps and continues even on failure.
"""
import os
import subprocess
import sys
from pathlib import Path

# Configuration
INSTALL_DIR = Path(r"C:\Users\aw789\autonomous-github-agent")
PYTHON_EXE = sys.executable


class Installer:
    """Coordinates the complete installation."""

    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.steps: list[tuple[str, str, callable]] = []
        self.results: dict[str, bool] = {}

    def header(self, text: str):
        """Print a header."""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)

    def section(self, text: str):
        """Print a section header."""
        print(f"\n{'─' * 70}")
        print(f"  {text}")
        print(f"{'─' * 70}")

    def success(self, text: str):
        """Print success message."""
        print(f"✅ {text}")
        self.success_count += 1

    def failure(self, text: str):
        """Print failure message."""
        print(f"❌ {text}")
        self.failure_count += 1

    def info(self, text: str):
        """Print info message."""
        print(f"ℹ️  {text}")

    def run_command(self, cmd: list[str], description: str) -> bool:
        """Run a shell command and return success status."""
        try:
            print(f"\n   Command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, cwd=str(INSTALL_DIR), capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                self.success(description)
                return True
            else:
                self.failure(description)
                if result.stderr:
                    print(f"   Error: {result.stderr[:500]}")
                return False
        except subprocess.TimeoutExpired:
            self.failure(f"{description} (timeout)")
            return False
        except Exception as e:
            self.failure(f"{description} - {e}")
            return False

    def import_and_run(self, module_name: str, description: str) -> bool:
        """Import a Python module and run its main() function."""
        try:
            print(f"\n   Module: {module_name}.py")
            print("   Function: main()")

            # Change to install directory
            os.chdir(INSTALL_DIR)
            sys.path.insert(0, str(INSTALL_DIR))

            # Import the module
            if module_name in sys.modules:
                del sys.modules[module_name]

            module = __import__(module_name)

            # Run main() if it exists
            if hasattr(module, "main") and callable(module.main):
                module.main()
                self.success(description)
                return True
            else:
                self.failure(f"{description} (no main function)")
                return False

        except Exception as e:
            self.failure(f"{description} - {str(e)[:100]}")
            import traceback

            traceback.print_exc()
            return False

    def step_1_quick_setup(self):
        """Step 1: Create directory structure."""
        self.section("STEP 1: Create Directories and Init Files")
        return self.import_and_run("quick_setup", "Created directories and init files")

    def step_2_core_files(self):
        """Step 2: Create core modules."""
        self.section("STEP 2: Create Core Modules")
        return self.import_and_run("create_core_files", "Created core modules")

    def step_3_agents(self):
        """Step 3: Create agent modules."""
        self.section("STEP 3: Create Agent Modules")
        return self.import_and_run("create_agents", "Created agent modules")

    def step_4_cli(self):
        """Step 4: Create CLI and tests."""
        self.section("STEP 4: Create CLI and Tests")
        return self.import_and_run("create_cli", "Created CLI and tests")

    def step_5_pip_install(self):
        """Step 5: Install package with pip."""
        self.section("STEP 5: Install Package (pip install -e .)")
        return self.run_command(
            [PYTHON_EXE, "-m", "pip", "install", "-e", "."],
            "Installed package with pip",
        )

    def step_6_verify(self):
        """Step 6: Run verification."""
        self.section("STEP 6: Verify Installation")
        try:
            os.chdir(INSTALL_DIR)
            sys.path.insert(0, str(INSTALL_DIR))

            if "verify_installation" in sys.modules:
                del sys.modules["verify_installation"]

            import verify_installation

            # Run verification function
            success = verify_installation.verify_installation()

            if success:
                self.success("Installation verified")
            else:
                print("\n⚠️  Some verification checks did not pass")
                self.info("See above for details")

            return success

        except Exception as e:
            self.failure(f"Verification - {str(e)[:100]}")
            return False

    def run_all(self):
        """Execute all installation steps."""
        os.chdir(INSTALL_DIR)

        self.header("AUTONOMOUS GITHUB AGENT - COMPLETE INSTALLATION")

        print(f"\nPython: {PYTHON_EXE}")
        print(f"Version: {sys.version}")
        print(f"Directory: {INSTALL_DIR}\n")

        # Execute all steps
        self.results["Step 1: Directories"] = self.step_1_quick_setup()
        self.results["Step 2: Core Files"] = self.step_2_core_files()
        self.results["Step 3: Agents"] = self.step_3_agents()
        self.results["Step 4: CLI"] = self.step_4_cli()
        self.results["Step 5: Pip Install"] = self.step_5_pip_install()
        self.results["Step 6: Verify"] = self.step_6_verify()

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print installation summary."""
        self.header("INSTALLATION SUMMARY")

        print("\nResults:\n")
        for step, success in self.results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {step}: {status}")

        print(f"\nTotal: {self.success_count} passed, {self.failure_count} failed\n")

        # Overall status
        all_passed = all(self.results.values())

        self.header("FINAL STATUS")

        if all_passed:
            print("\n✅ INSTALLATION COMPLETE!")
            print("\nNext steps:")
            print("  1. Edit the .env file and add your GitHub API token")
            print("  2. Add your LLM provider credentials (OpenAI, Anthropic, etc.)")
            print("  3. Run: autonomous-agent --help")
            print("  4. Try: autonomous-agent health-check --repo owner/repo\n")
        else:
            print("\n⚠️  Some steps failed. See details above.")
            print("\nFailed steps:")
            for step, success in self.results.items():
                if not success:
                    print(f"  - {step}")
            print("\nYou may need to:")
            print("  - Check the error messages above")
            print("  - Ensure all dependencies are installed")
            print("  - Run: pip install -r requirements.txt\n")

        return 0 if all_passed else 1


def main():
    """Main entry point."""
    installer = Installer()
    exit_code = installer.run_all()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
