# Repository Consolidation Roadmap

**Project:** GitHub Autopilot + Multi-Repo Consolidation
**Start Date:** January 4, 2026
**Owner:** labgadget015-dotcom
**Status:** 🟢 In Progress

---

## 🎯 Executive Summary

Consolidate 25+ repos into **3 core products**:
1. **GitHub Autopilot** (flagship) - automated daily repo summaries
2. **ai-automation-engine** (platform) - shared agent infrastructure
3. **SmartHomeAI** (secondary) - real-world dogfood testbed

Pause/archive all other repos until these 3 are production-ready and delivering daily value.

---

## 📊 Current State Assessment

### Repository Inventory (from GitHub Dashboard)

**Critical - Core Product Repos (3)**
- `autonomous-github-agent` - 40 issues, 1 PR, Python 97%
  - Status: Active development, test coverage issues
  - Action: Rename → **GitHub Autopilot**, make flagship

- `github-multi-agent-system` - 2 issues, 0 PRs, Python 100%
  - Status: Recently active (2 weeks), documentation + roadmap
  - Action: Merge into GitHub Autopilot + ai-automation-engine

- `ai-automation-engine` - 3 issues, 0 PRs, Python 41%, HTML 28%
  - Status: Platform backbone, needs agent orchestration (#3)
  - Action: Make canonical platform for all products

**Medium Priority (1)**
- `micro-bot-workflow-template` - 0 issues, Python templates
  - Status: Dormant
  - Action: Keep as workflow library, low touch

**Pause/Archive Until v0.2+ (4+)**
- `AI-crypto-trading-bot`, `crypto-trading-bot`
- `ai-ops-desk`
- `ViralVideo`, YouTube analytics repos
- `ai-lead-brain`
- `SmartHomeAI` (10 issues) - pause for now, resume post-Autopilot

---

## 🗺️ Consolidation Strategy

###  Phase 1: GitHub Autopilot v0 (Jan 4-11, 2026) ✅ CURRENT

**Goal:** Ship working daily summary tool

**Deliverables:**
- [x] Issue #42 created
- [x] SPEC_v0.md created
- [x] autopilot/config.yaml created
- [ ] autopilot/autopilot.py (core script)
- [ ] requirements.txt, .env.example
- [ ] DAILY_USAGE.md template
- [ ] README_AUTOPILOT.md
- [ ] First working daily summary generated

**Key Files to Create:**
```
autopilot/
├── __init__.py
├── autopilot.py          # Main script
├── config.yaml           # [DONE]
├── github_client.py      # API wrapper
├── analyzer.py           # Priority scoring
└── formatter.py          # Markdown output

requirements.txt        # PyGithub, pyyaml, python-dotenv
.env.example            # GITHUB_TOKEN template
DAILY_USAGE.md          # Dogfooding log
README_AUTOPILOT.md     # Usage instructions
```

**Success Criteria:**
- `python autopilot/autopilot.py` generates markdown summary in < 60s
- Used daily for 7 days (Jan 11-18)
- DAILY_USAGE.md has 7 entries with feedback

---

### 🔗 Phase 2: Platform Integration (Jan 18-25, 2026)

**Goal:** Wire GitHub Autopilot into ai-automation-engine platform

**Actions:**
1. **Implement ai-automation-engine#3** - Core AI Agent Orchestration
   - Agent lifecycle: init, run, cleanup
   - Shared logging, config, error handling
   - GitHub Autopilot becomes first "agent" client

2. **Merge micro-agent libraries**
   - Consolidate `micro-proactive-agents` + `MicroAgentFramework` → one canonical lib in ai-automation-engine
   - GitHub Autopilot uses this for scheduling + proactive triggers

3. **Token optimizer integration**
   - Merge `ai-agent-token-optimizer` + `advanced-agent-token-optimizer` → LLM gateway
   - GitHub Autopilot uses for LLM-based priority analysis (v0.2+)

**Deliverables:**
- `ai-automation-engine/agents/github_autopilot/` module
- Shared `AgentBase` class all products inherit from
- Centralized logging → all agents write to same format
- GitHub Autopilot v0.2 runs via platform, not standalone

---

### 📦 Phase 3: Multi-Agent System Merge (Feb 1-8, 2026)

**Goal:** Fold github-multi-agent-system features into platform + Autopilot

**Actions:**
1. **Extract useful agents from github-multi-agent-system:**
   - `DocumentationAgent` (#4) → add to GitHub Autopilot as "doc health check"
   - `CodeHealthAgent`, `WorkflowAgent`, `IssueAgent` → optional Autopilot plugins

2. **Archive github-multi-agent-system repo**
   - Mark as "Merged into GitHub Autopilot + ai-automation-engine"
   - Link to new locations in README

**Deliverables:**
- GitHub Autopilot has pluggable agent system
- 3-4 specialized agents available as opt-in features
- Single repo consolidation: autonomous-github-agent → **github-autopilot**

---

### 🔥 Phase 4: Dogfood with SmartHomeAI (Feb 15-28, 2026)

**Goal:** Stress-test platform with real-world non-GitHub use case

**Actions:**
1. **Resume SmartHomeAI development**
   - Build on ai-automation-engine platform
   - Use micro-agent framework for home automation agents
   - Real sensors, real actuators, real failure modes

2. **Extract learnings → platform improvements**
   - Error recovery patterns
   - Agent scheduling under resource constraints
   - Multi-agent coordination

**Success Criteria:**
- SmartHomeAI runs autonomously for 7 days without intervention
- Platform handles 10+ concurrent agents
- GitHub Autopilot + SmartHomeAI both stable

---

## ⛔ Paused Repos - Decision Framework

### When to Resume:
Only resume a paused repo if:
1. GitHub Autopilot is in daily use (7+ days)
2. ai-automation-engine platform is stable
3. The paused repo has a clear paying customer OR strategic integration need

### Repo-by-Repo Decision:

**Trading Bots** (`AI-crypto-trading-bot`, `crypto-trading-bot`)
- Resume if: Active trading strategy + capital to deploy
- Merge: Combine into single `crypto-agent` using platform

**RevOps** (`ai-lead-brain`, `ai-ops-desk`)
- Resume if: Agency client ready to pilot
- Merge: Single "RevOps Autopilot" product

**YouTube Analytics** (multiple repos)
- Resume if: Creator/agency partnership for viral research
- Merge: Single "Viral Intelligence" SaaS

---

## 📝 Implementation Checklist

### Week 1 (Jan 4-11): GitHub Autopilot v0 ✅ IN PROGRESS
- [x] Create Issue #42
- [x] Write SPEC_v0.md
- [x] Create autopilot/config.yaml
- [ ] Write autopilot/autopilot.py (200-300 lines)
- [ ] Write github_client.py wrapper
- [ ] Write analyzer.py (priority scoring)
- [ ] Write formatter.py (markdown generation)
- [ ] Create requirements.txt
- [ ] Create .env.example
- [ ] Create README_AUTOPILOT.md
- [ ] Create DAILY_USAGE.md template
- [ ] Generate first daily summary
- [ ] Commit all code to main branch

### Week 2 (Jan 11-18): Dogfooding
- [ ] Run autopilot daily, log feedback in DAILY_USAGE.md
- [ ] Fix bugs, tune priority scoring
- [ ] Add any missing repos to config.yaml
- [ ] Decide v0.2 features based on real usage

### Week 3 (Jan 18-25): Platform Integration
- [ ] Implement ai-automation-engine#3 (Core Agent Orchestration)
- [ ] Create AgentBase class
- [ ] Migrate GitHub Autopilot to use platform
- [ ] Consolidate micro-agent libraries
- [ ] Test GitHub Autopilot v0.2 via platform

### Week 4 (Jan 25-Feb 1): Multi-Agent Merge
- [ ] Extract agents from github-multi-agent-system
- [ ] Add as optional plugins to GitHub Autopilot
- [ ] Archive github-multi-agent-system repo
- [ ] Rename autonomous-github-agent → github-autopilot

---

## 📊 Success Metrics

### Quantitative
- **Repo Count:** 25+ → 3 core products (88% reduction)
- **Daily Active Use:** GitHub Autopilot used 7/7 days
- **Runtime:** Daily summary < 60 seconds
- **Code Reuse:** 80%+ shared code via ai-automation-engine platform

### Qualitative
- **Focus:** Can describe "the product" in one sentence
- **Velocity:** Ship features to ONE repo instead of context-switching across 5
- **Dogfooding:** GitHub Autopilot replaces manual dashboard checking
- **Monetization Clarity:** Clear path to revenue for each of 3 products

---

## 🔗 Key Links

- [Issue #42: GitHub Autopilot v0](https://github.com/labgadget015-dotcom/autonomous-github-agent/issues/42)
- [SPEC_v0.md](https://github.com/labgadget015-dotcom/autonomous-github-agent/blob/main/SPEC_v0.md)
- [autopilot/config.yaml](https://github.com/labgadget015-dotcom/autonomous-github-agent/blob/main/autopilot/config.yaml)
- [ai-automation-engine#3: Core Agent Orchestration](https://github.com/labgadget015-dotcom/ai-automation-engine/issues/3)
- [github-multi-agent-system#2: Multi-Agent Roadmap Q4 2025](https://github.com/labgadget015-dotcom/github-multi-agent-system/issues/2)

---

**Last Updated:** 2026-01-04
**Next Review:** 2026-01-11 (Post v0 ship)
**Status:** 🟢 On Track
