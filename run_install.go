package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	// Change to the directory
	dir := filepath.Join("C:", "Users", "aw789", "autonomous-github-agent")
	if err := os.Chdir(dir); err != nil {
		fmt.Printf("Error changing directory: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Running installation script...")
	fmt.Println("Directory:", dir)
	fmt.Println()

	// Run the Python installation script
	cmd := exec.Command("python", "install.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	if err := cmd.Run(); err != nil {
		fmt.Printf("Error running installation: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("\nInstallation script completed.")
}
