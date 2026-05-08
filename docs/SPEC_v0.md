# GitHub Autopilot v0 Specification

**Project:** Autonomous GitHub Agent → GitHub Autopilot
**Version:** v0
**Status:** Build Sprint (Jan 4-11, 2026)
**Owner:** labgadget015-dotcom
**Issue:** [#42](https://github.com/labgadget015-dotcom/autonomous-github-agent/issues/42)

---

## 🎯 Mission

Replace manual GitHub dashboard scanning with one automated daily summary command that tells you:
- What changed today across all your active repos
- What's blocked and needs attention
- Top 3 things to work on

## 📋 Definition of Done

One script/command that:
1. Reads **open issues**, **open PRs**, and **recent commits** from target repositories
2. Outputs a single **Markdown summary** with:
   - Today's changes (commits, new issues, new PRs)
   - What's blocked (stale PRs, urgent issues)
   - "Top 3 priorities" recommendation
3. Can be run with: `python autopilot.py` or `make summary`
4. Takes < 60 seconds to complete

## 🎯 Target Repositories

From GitHub Dashboard "Top repositories":

```yaml
repositories:
  - name: autonomous-github-agent
    owner: labgadget015-dotcom
    priority: critical
    issues: 40
    prs: 1
    notes: "Test coverage issues + optimization PR"

  - name: github-multi-agent-system
    owner: labgadget015-dotcom
    priority: critical
    issues: 2
    prs: 0
    notes: "Documentation agent + Q4 roadmap"

  - name: ai-automation-engine
    owner: labgadget015-dotcom
    priority: critical
    issues: 3
    prs: 0
    notes: "Platform backbone - agent orchestration"

  - name: micro-bot-workflow-template
    owner: labgadget015-dotcom
    priority: medium

  - name: AI-crypto-trading-bot
    owner: labgadget015-dotcom
    priority: low

  - name: ai-ops-desk
    owner: labgadget015-dotcom
    priority: low

  - name: ViralVideo
    owner: labgadget015-dotcom
    priority: low
```

## 📤 Output Format

### Example Daily Summary

```markdown
# GitHub Autopilot Daily Summary
**Date:** 2026-01-04
**Repos Scanned:** 7
**Runtime:** 23s

---

## 🚨 Top 3 Priorities

1. **[autonomous-github-agent]** Merge PR #41 (Phase 1 & 3 optimization) - 11 tasks, opened last week
2. **[autonomous-github-agent]** Fix test coverage issues (#16-#39) - 24 automated urgent issues
3. **[ai-automation-engine]** Implement Core AI Agent Orchestration (#3) - blocking multi-repo integration

---

## 📊 Activity Summary

### Critical Repos

#### autonomous-github-agent (40 issues, 1 PR)
- **New Today:** Workflow concurrency control added (last week)
- **Open PRs:** #41 [OPTIMIZATION] Phase 1 & 3 Implementation (11 tasks, needs review)
- **Urgent Issues:** 24x Test Coverage Below Threshold (automated, Dec 1)
- **Recent Enhancement:** #40 Performance Optimization Plan (last week)

#### github-multi-agent-system (2 issues, 0 PRs)
- **Open Issues:**
  - #4 [Phase 1] Implement DocumentationAgent.check_documentation() - AI-Powered Doc Analysis
  - #2 🚀 Multi-Agent System Implementation Roadmap Q4 2025
- **Recent Activity:** Monitoring & observability config added (2 weeks ago)

#### ai-automation-engine (3 issues, 0 PRs)
- **Open Issues:**
  - #5 [PROJECT] Set Up GitHub Projects Board with Automated Workflows
  - #4 [TEST] Increase Code Coverage to 80%+ with Integration Tests
  - #3 [FEATURE] Core AI Agent Orchestration System with Multi-Agent Framework
- **Recent Activity:** Dashboard README created (last month)

### Medium Priority

#### micro-bot-workflow-template
- No recent activity

### Low Priority (Paused)

#### AI-crypto-trading-bot, ai-ops-desk, ViralVideo
- Paused per consolidation strategy

---

## 🔗 Related Issues
- See: [#42 GitHub Autopilot v0 Consolidation](https://github.com/labgadget015-dotcom/autonomous-github-agent/issues/42)

```

## 🏗️ Technical Architecture

### Core Script: `autopilot.py`

```python
# High-level structure
class GitHubAutopilot:
    def __init__(self, config_path="config.yaml"):
        self.repos = load_target_repos(config_path)
        self.github_client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))

    def fetch_repo_data(self, repo):
        """Fetch issues, PRs, recent commits for one repo"""
        return {
            "issues": self.github_client.get_issues(repo, state="open"),
            "prs": self.github_client.get_pulls(repo, state="open"),
            "commits": self.github_client.get_commits(repo, since="24h")
        }

    def analyze_priorities(self, all_data):
        """Generate top 3 priorities across all repos"""
        # Score by: urgency labels, PR age, issue count, recent activity
        pass

    def generate_summary(self, all_data, priorities):
        """Output markdown summary"""
        pass

    def run(self):
        """Main execution flow"""
        all_data = {repo: self.fetch_repo_data(repo) for repo in self.repos}
        priorities = self.analyze_priorities(all_data)
        summary = self.generate_summary(all_data, priorities)
        print(summary)
        return summary
```

### Dependencies

```txt
PyGithub==2.1.1
pyyaml==6.0.1
python-dotenv==1.0.0
```

### Configuration: `config.yaml`

```yaml
repos:
  - owner: labgadget015-dotcom
    name: autonomous-github-agent
    priority: critical
  - owner: labgadget015-dotcom
    name: github-multi-agent-system
    priority: critical
  - owner: labgadget015-dotcom
    name: ai-automation-engine
    priority: critical
  # ... etc

output:
  format: markdown
  file: DAILY_SUMMARY.md

analysis:
  priority_weights:
    urgent_label: 10
    pr_age_days: 2
    issue_count: 1
    recent_activity: 3
```

## 🚫 Hard Constraints (7 days)

1. **NO new repos** during build
2. **NO UI work** - CLI only
3. **NO extra agent types** unless absolutely required
4. **NO non-critical refactors**
5. Direct GitHub API calls OK (PyGithub) - keep it simple
6. **Must complete by:** January 11, 2026

## ✅ Acceptance Criteria

- [ ] `python autopilot.py` generates Markdown summary
- [ ] Summary includes issues, PRs, commits for all 7 target repos
- [ ] Summary provides "Top 3 priorities" with reasoning
- [ ] Runtime < 60 seconds
- [ ] Used in daily workflow for 7 consecutive days (Jan 11-18)
- [ ] `DAILY_USAGE.md` has feedback from all 7 days
- [ ] All critical repo data is accurate (autonomous-github-agent, github-multi-agent-system, ai-automation-engine)

## 🔄 Integration with Platform

### Phase 1: Standalone (v0)
- Direct PyGithub API calls
- Minimal dependencies
- Focus on speed and reliability

### Phase 2: Platform Integration (v0.2+)
- Use `ai-automation-engine` for agent lifecycle
- Integrate with `micro-agent` framework
- Add token optimizer for LLM-based priority analysis

## 📅 Timeline

| Date | Milestone | Deliverable |
|------|-----------|-------------|
| Jan 4 | Kickoff | Issue #42 created, SPEC_v0.md |
| Jan 5-6 | Core Build | autopilot.py, config.yaml |
| Jan 7-8 | Testing | End-to-end flow, fix bugs |
| Jan 9-10 | Polish | README_AUTOPILOT.md, DAILY_USAGE.md template |
| Jan 11 | Ship v0 | First production daily summary |
| Jan 11-18 | Dogfood | Use daily, log feedback |
| Jan 18 | Review | Decide v0.2 features based on DAILY_USAGE.md |

## 📝 Success Metrics

**Quantitative:**
- Runtime < 60s ✅
- 100% repo coverage (7/7) ✅
- Used 7 days in a row ✅

**Qualitative:**
- Replaces manual dashboard checking
- Actionable "Top 3" actually guides daily work
- Feedback in DAILY_USAGE.md leads to clear v0.2 roadmap

## 🔗 Related Documentation

- [Issue #42: GitHub Autopilot v0](https://github.com/labgadget015-dotcom/autonomous-github-agent/issues/42)
- [ai-automation-engine#3: Core AI Agent Orchestration](https://github.com/labgadget015-dotcom/ai-automation-engine/issues/3)
- [github-multi-agent-system#2: Multi-Agent Roadmap Q4 2025](https://github.com/labgadget015-dotcom/github-multi-agent-system/issues/2)

---

**Last Updated:** 2026-01-04
**Next Review:** 2026-01-11 (v0 ship date)
