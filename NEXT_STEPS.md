# Quick Configuration & Testing Guide

## 1️⃣ Configure Your Tokens (NOW)

Open the `.env` file in: `C:\Users\aw789\autonomous-github-agent\.env`

Replace these lines with your actual tokens:
```env
GITHUB_TOKEN=ghp_your_actual_github_token_here
OPENAI_API_KEY=sk_your_actual_openai_key_here
```

Save and close.

## 2️⃣ Verify Configuration (30 seconds)

Open Command Prompt in: `C:\Users\aw789\autonomous-github-agent`

Run:
```cmd
autonomous-agent config-check
```

You should see:
✓ GitHub Token: Set
✓ LLM API Key: Set
✓ Configuration valid

## 3️⃣ List Available Agents

```cmd
autonomous-agent list-agents
```

You should see all 7 agents listed.

## 4️⃣ Test on a Real Repository

Try these commands:

### Health Check (Safe - Read-Only)
```cmd
autonomous-agent health-check --repo octocat/Hello-World
```

### Analyze Repository
```cmd
autonomous-agent analyze --repo YOUR_USERNAME/YOUR_REPO
```

### Review Pull Requests (if any exist)
```cmd
autonomous-agent review --repo YOUR_USERNAME/YOUR_REPO
```

### View Audit Logs
```cmd
autonomous-agent logs --limit 10
```

## 5️⃣ Advanced Usage

### Run Specific Agent
```cmd
autonomous-agent analyze --repo owner/repo --agent health
autonomous-agent analyze --repo owner/repo --agent security
```

### Monitor Continuously
```cmd
autonomous-agent monitor --repo owner/repo
```

## 🎯 What Each Agent Does

- **health_monitor** - Repository metrics, stale branches, missing files
- **code_reviewer** - Automated PR reviews with security checks
- **issue_manager** - Auto-label and triage issues
- **branch_manager** - Clean up old branches
- **security_scanner** - Detect secrets and vulnerabilities
- **workflow_optimizer** - Analyze GitHub Actions
- **documentation_generator** - Update docs automatically

## 📊 Check Results

After running commands, check:
```cmd
autonomous-agent logs
```

## 🆘 Troubleshooting

**"Config check fails"**
- Make sure tokens are correctly pasted in .env
- No extra spaces or quotes

**"Command not found"**
- Reopen Command Prompt
- Or run: `pip install -e .` again

**"GitHub API error"**
- Check token has `repo` scope
- Verify token at: https://github.com/settings/tokens

**"OpenAI API error"**
- Verify API key
- Check you have credits

## ✅ You're Ready!

Start with a test repository to see the agents in action!

```cmd
autonomous-agent health-check --repo octocat/Hello-World
```
