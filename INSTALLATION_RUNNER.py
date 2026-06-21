#!/usr/bin/env python
"""
Master Installation Runner for Autonomous GitHub Agent
Orchestrates all installation steps in sequence
"""
import os
import subprocess
import sys
import traceback
from pathlib import Path

# Ensure we're in the right directory
INSTALL_DIR = Path(r"C:\Users\aw789\autonomous-github-agent")
os.chdir(INSTALL_DIR)
sys.path.insert(0, str(INSTALL_DIR))


class InstallationRunner:
    """Manages the complete installation process."""

    def __init__(self):
        self.results = {}
        self.start_dir = os.getcwd()

    def log(self, message, level="INFO"):
        """Log a message."""
        prefix = f"[{level}]" if level != "INFO" else ""
        print(f"{prefix} {message}")

    def run_python_module(self, module_name, description):
        """Run a Python script as a module and capture output."""
        self.log(f"\n{'='*70}", "")
        self.log(f"Step: {description}", "")
        self.log(f"Module: {module_name}", "")
        self.log(f"{'='*70}", "")

        try:
            # Import and run the module
            if module_name in sys.modules:
                del sys.modules[module_name]

            module = __import__(module_name)

            # Look for main() function
            if hasattr(module, "main") and callable(module.main):
                self.log(f"Executing {module_name}.main()...", "")
                module.main()
                self.log(f"✓ {description} - SUCCESS", "OK")
                self.results[description] = True
                return True
            else:
                self.log(f"✗ No main() function found in {module_name}", "ERROR")
                self.results[description] = False
                return False

        except Exception as e:
            self.log(f"✗ {description} - FAILED", "ERROR")
            self.log(f"Error: {e}", "ERROR")
            traceback.print_exc()
            self.results[description] = False
            return False

    def run_pip_install(self):
        """Run pip install -e ."""
        self.log(f"\n{'='*70}", "")
        self.log("Step: Install package with pip", "")
        self.log(f"{'='*70}", "")

        try:
            cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
            self.log(f"Running: {' '.join(cmd)}", "")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.stdout:
                print(result.stdout)

            if result.returncode == 0:
                self.log("✓ Package installation - SUCCESS", "OK")
                self.results["Step 5: Package installation (pip install -e .)"] = True
                return True
            else:
                self.log("✗ Package installation - FAILED", "ERROR")
                if result.stderr:
                    self.log(f"Error: {result.stderr}", "ERROR")
                self.results["Step 5: Package installation (pip install -e .)"] = False
                return False

        except subprocess.TimeoutExpired:
            self.log("✗ Installation timed out", "ERROR")
            self.results["Step 5: Package installation (pip install -e .)"] = False
            return False
        except Exception as e:
            self.log(f"✗ Installation failed: {e}", "ERROR")
            traceback.print_exc()
            self.results["Step 5: Package installation (pip install -e .)"] = False
            return False

    def run_verification(self):
        """Run verification script."""
        self.log(f"\n{'='*70}", "")
        self.log("Step: Verify Installation", "")
        self.log(f"{'='*70}", "")

        try:
            if "verify_installation" in sys.modules:
                del sys.modules["verify_installation"]

            import verify_installation

            if hasattr(verify_installation, "main"):
                verify_installation.main()
                self.log("✓ Verification - SUCCESS", "OK")
                self.results["Step 6: Verify installation"] = True
                return True
            else:
                self.log("✗ No main() in verify_installation", "ERROR")
                self.results["Step 6: Verify installation"] = False
                return False

        except Exception as e:
            self.log(f"✗ Verification failed: {e}", "ERROR")
            traceback.print_exc()
            self.results["Step 6: Verify installation"] = False
            return False

    def print_summary(self):
        """Print installation summary."""
        print("\n" + "=" * 70)
        print("INSTALLATION SUMMARY")
        print("=" * 70 + "\n")

        for step, success in self.results.items():
            status = "✓ PASSED" if success else "✗ FAILED"
            print(f"{step}: {status}")

        all_success = all(self.results.values())

        print("\n" + "=" * 70)
        if all_success:
            print("✓ ALL STEPS COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("\nThe Autonomous GitHub Agent is ready to use!")
            print("\nNext steps:")
            print("1. Edit the .env file and add your GitHub API token")
            print("2. Add your LLM provider credentials (OpenAI, Anthropic, etc.)")
            print("3. Run the CLI: python -m autonomous_agent.cli.main --help")
            print("4. Check logs directory for execution logs")
        else:
            print("⚠ SOME STEPS FAILED - CHECK OUTPUT ABOVE")
            print("=" * 70)
            print("\nFailed steps:")
            for step, success in self.results.items():
                if not success:
                    print(f"  - {step}")

        print()

    def run_installation(self):
        """Execute the complete installation."""
        print("\n" + "=" * 70)
        print("AUTONOMOUS GITHUB AGENT - INSTALLATION")
        print("=" * 70)
        print(f"Python: {sys.executable}")
        print(f"Version: {sys.version}")
        print(f"Directory: {self.start_dir}\n")

        # Step 1: quick_setup.py
        self.run_python_module(
            "quick_setup", "Step 1: Create directories and init files"
        )

        # Step 2: create_core_files.py
        self.run_python_module("create_core_files", "Step 2: Create core modules")

        # Step 3: create_agents.py
        self.run_python_module("create_agents", "Step 3: Create agent modules")

        # Step 4: create_cli.py
        self.run_python_module("create_cli", "Step 4: Create CLI and tests")

        # Step 5: pip install
        self.run_pip_install()

        # Step 6: Verify
        self.run_verification()

        # Print summary
        self.print_summary()

        # Return appropriate exit code
        return 0 if all(self.results.values()) else 1


def main():
    """Main entry point."""
    runner = InstallationRunner()
    exit_code = runner.run_installation()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
