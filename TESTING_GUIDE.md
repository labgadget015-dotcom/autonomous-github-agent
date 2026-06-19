# 🧪 Testing Your Installation

## Quick Test Commands

Open Command Prompt in: `C:\Users\aw789\autonomous-github-agent`

### Test 1: Verify Configuration
```cmd
autonomous-agent config-check
```

**Expected output:**
```
✓ GitHub Token: Set
✓ LLM Provider: openai
✓ LLM API Key: Set
✓ Automation Level: semi-auto
✓ Enabled Agents: 7
```

---

### Test 2: List Agents
```cmd
autonomous-agent list-agents
```

**Expected output:** Table showing 7 agents

---

### Test 3: Health Check (Safe Test)
```cmd
autonomous-agent health-check --repo octocat/Hello-World
```

**Expected output:**
- "Running health check on octocat/Hello-World..."
- Repository metrics table
- "Health check complete!"

---

### Test 4: Full Analysis
```cmd
autonomous-agent analyze --repo octocat/Hello-World
```

**Expected output:**
- Health report with stars, forks, open issues
- Recommendations (if any)
- Security scan results

---

### Test 5: View Logs
```cmd
autonomous-agent logs --limit 5
```

**Expected output:** Table showing recent agent actions

---

## Automated Testing

**Just run this:**
```
TEST_INSTALLATION.bat
```

It will run all 5 tests automatically and tell you if everything works!

---

## What If Tests Fail?

### Config-Check Fails
**Problem:** "GitHub token not configured" or "LLM API key not configured"

**Solution:**
1. Open `.env` file
2. Check tokens are pasted correctly
3. No quotes, no spaces before/after =
4. Save the file
5. Try again

### Command Not Found
**Problem:** "autonomous-agent is not recognized..."

**Solution:**
```cmd
pip install -e .
```
Then close and reopen Command Prompt

### GitHub API Error
**Problem:** "401 Unauthorized" or "403 Forbidden"

**Solution:**
- Check GitHub token has `repo` scope
- Verify at: https://github.com/settings/tokens
- Token may have expired - create a new one

### OpenAI API Error
**Problem:** "Invalid API key" or "Insufficient quota"

**Solution:**
- Check API key is correct in `.env`
- Verify you have credits: https://platform.openai.com/usage
- Or switch to Anthropic in `.env`: `LLM_PROVIDER=anthropic`

---

## Next Steps After Testing

Once all tests pass:

1. **Try on your repository:**
   ```cmd
   autonomous-agent analyze --repo YOUR_USERNAME/YOUR_REPO
   ```

2. **Review pull requests:**
   ```cmd
   autonomous-agent review --repo YOUR_USERNAME/YOUR_REPO
   ```

3. **Explore all commands:**
   ```cmd
   autonomous-agent --help
   ```

4. **Set up automation:**
   - Copy `workflows/*.yml` to your repo's `.github/workflows/`
   - Agents will run automatically on PRs and schedule

---

## Success Criteria

✅ Config check passes  
✅ All 7 agents listed  
✅ Health check completes without errors  
✅ Logs show agent activity  
✅ Can analyze test repository  

**If all above work → You're ready to use it on real repos!** 🚀
