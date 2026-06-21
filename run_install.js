const { execSync } = require('child_process');
const path = require('path');
const process = require('process');

// Change to the autonomous-github-agent directory
const agentDir = 'C:\\Users\\aw789\\autonomous-github-agent';
process.chdir(agentDir);

console.log('========================================');
console.log('  Autonomous GitHub Agent Installation');
console.log('========================================\n');
console.log(`Working directory: ${agentDir}\n`);

try {
    // Run the Python installation script
    console.log('Executing install.py...\n');
    execSync('python install.py', {
        stdio: 'inherit',
        cwd: agentDir
    });

    console.log('\n✓ Installation completed successfully!');
} catch (error) {
    console.error('\n✗ Installation failed:', error.message);
    process.exit(1);
}
