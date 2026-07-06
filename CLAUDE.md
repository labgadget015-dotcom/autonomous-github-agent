# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Context

This shell manages the **GadgetLab autonomous GitHub agent pipeline**. There are three areas of work:

| Area | Location |
|------|----------|
| Python codebase | `/home/ai/autonomous-github-agent/` (also at https://github.com/labgadget015-dotcom/autonomous-github-agent) |
| n8n workflows | https://gadgetlab.app.n8n.cloud — use n8n MCP tools to inspect/modify |
| Obsidian vault | `/home/ai/obsidian-ai-architect-vault/` — project notes and architecture docs |

**User email:** labgadget015@gmail.com

## Development Commands (run from `/home/ai/autonomous-github-agent/`)

Activate the venv first, or prefix commands with `.venv/bin/`:

```bash
source .venv/bin/activate
pip install -r requirements.txt          # install all deps if venv is missing packages
```

```bash
pytest tests/ -v                         # full suite (unit + integration, coverage on by default)
pytest tests/unit/test_core.py -v        # single unit test file
pytest tests/test_core.py -v             # single integration test file
pytest -m "not slow" -v                  # skip slow tests
pytest -k "test_github" -v              # filter by name
pre-commit run --all-files               # run all pre-commit hooks (fail_fast: true — stops on first failure)
ruff check . --fix                       # lint + auto-fix (covers isort, bugbear, pyupgrade)
black .github/scripts/ core/ agents/     # format
mypy core/ agents/ autopilot/            # type-check (ignores missing stubs)
bandit -r core agents autopilot          # security scan
python run_overseer.py                   # run the repository overseer manually
```

**Makefile shortcuts** (Docker-based):
```bash
make test-local      # fast local test run
make test-full       # complete suite
make lint            # pylint + flake8
make format          # black + isort
make security        # bandit scan → bandit-report.json
make analyze         # parallel code analysis
make validate        # validate all implementations
```

pytest configuration is in `pytest.ini`. The `pytest` run enforces ≥55% coverage (`--cov-fail-under=55` in `pytest.ini addopts`); `pyproject.toml [tool.coverage.report]` sets `fail_under=70` for standalone `coverage report` runs. asyncio mode is `auto`.

**Test layout:** `tests/unit/` holds 40+ focused unit tests (one per module). `tests/` root holds broader integration/smoke tests (`test_core.py`, `test_overseer.py`, etc.).

## Architecture Overview

### Three-layer pipeline

```
GitHub events
    │
    ▼
n8n: GitHub Event Router (oijizIGJtRzBG94Z)
  - Validates HMAC signatures on incoming webhooks
  - Filters actionable events (issues + push)
    │
    ▼
n8n: DRC Agent Loop (Wlfhgk4sUfXJcU4D)
  - Dreamer / Realist / Critic pattern (three Claude Sonnet nodes)
  - Webhook: https://gadgetlab.app.n8n.cloud/webhook/github-agent-loop
  - Average run ~90 s
    │
    ▼
GitHub Actions (12 workflows in .github/workflows/)
  - ai_agent_workflow.yml: main pipeline — parallel test matrix (Py 3.10/3.11/3.12) + code quality
  - security_scan.yml, code-quality-optimized.yml, pre-commit-ci.yml
  - repository-overseer.yml: full-stack repo management via overseer/ — runs weekly (Sunday midnight) and on push to main affecting `.py`, `requirements.txt`, or workflows
  - elite_copilot.yml, agent_dispatcher.yml, dry_run_gate.yml
```

### Python package layout

```
core/           — shared infrastructure (BaseAgent, GitHubClient, LLMClient,
                  PolicyEngine, AuditLogger, RiskScorer, IdempotencyGuard)
agents/         — orchestrator_agent.py (extends BaseAgent)
overseer/       — autonomous repo management: code_analyzer, issue_triager,
                  automation_engine, cicd_optimizer, dependency_manager,
                  doc_generator, orchestrator, monitor
autopilot/      — daily summaries; autopilot.py + ai_optimization/ sub-package
                  (NLP filter, ML priority scorer, anomaly detector, cache);
                  behavior configured via autopilot/config.yaml
.github/scripts/ — 40+ standalone scripts invoked by GitHub Actions workflows
tests/          — top-level integration tests + tests/unit/ for all modules
config/         — agent_config.yaml, policies.yaml, code_standards.yaml
```

**Key design patterns:**
- All agents extend `core/agent_base.py:BaseAgent` — lifecycle: validate → policy check → execute → audit log
- `core/llm_provider.py` abstracts Anthropic/OpenAI; `.github/scripts/llm_router.py` adds local-model routing — set `LOCAL_LLM_URL` (default `http://localhost:1234/v1`) to route simple/low-severity tasks to a local model at zero cost; complex/critical tasks always go to cloud
- `core/policy_engine.py` enforces `config/policies.yaml` before any destructive GitHub action; protected paths that require approval include `.github/workflows/`, `config/`, and `core/`
- `core/idempotency.py` prevents duplicate executions
- `core/risk_scorer.py` gates actions — score bands: 0–2.9 LOW (auto-merge ok), 3–5.9 MEDIUM (needs review), 6–7.9 HIGH (block auto-merge), 8–10 CRITICAL (block + notify); default threshold is 4.0 (`pyproject.toml [tool.autonomous-agent]`)
- Dry-run mode is **on by default** (`dry_run = true`) — set `require_approval = true` to confirm before write actions
- LLM cost cap: `llm_max_cost_usd = 1.0` per run (pyproject.toml); autopilot generates daily summaries to `DAILY_SUMMARY.md` using `autopilot/autopilot.py`

### Reusable action (`action.yml`)

The repo also ships as a publishable composite GitHub Action. External repos can consume it via `uses: labgadget015-dotcom/autonomous-github-agent@main`. Inputs: `analysis_mode` (parallel/sequential/auto), `local_llm_enabled`, `local_llm_endpoint` (default `http://localhost:11434` — Ollama), `complexity_threshold`, `severity_threshold`. Note the URL differs from the in-repo default (`http://localhost:1234/v1` in `llm_router.py`).

### Task context (`context.json`)

At runtime the agent reads a `context.json` file (see `context.json.example`). Shape:
```json
{ "repository": "owner/repo", "event_name": "pull_request", "ref": "refs/heads/main",
  "actor": "username", "pull_request": { "number": 1, "title": "...", "base": "main", "head": "feature" },
  "github_api_url": "https://api.github.com", "timestamp": "..." }
```

### n8n constraints

- Sessions expire after ~30–60 min of inactivity; autosave silently fails with 401. Claude cannot re-authenticate — Gadget must log in.
- Canvas drag-and-drop is unreliable; prefer JavaScript/Pinia store manipulation when automating node placement.
- "Notify Slack — DRC Result" node uses HTTP Request → Slack Incoming Webhook (no OAuth). Channel: `#drc-recommendations` (gadgetai.slack.com). Webhook secret stored as `SLACK_WEBHOOK_URL` GitHub secret.
- **DRC webhook auth (`x-gadgetlab-token`):** the DRC Agent Loop's `Prepare Input` node gates all real traffic on a static `x-gadgetlab-token` header; the Event Router's "Forward to Agent Loop" node is the sole legitimate sender. The token value lives **only in n8n** (embedded literals in both nodes — never committed to this public repo, never a GitHub secret). Last rotated **2026-07-06**; the old value is retired (rejected with `Unauthorized`). To rotate: set the same new value in both nodes and publish both. Health-check pings are exempt — the `Route Health Ping` IF node short-circuits them to a `Pong` 200 before the gate, so `n8n-health-check.yml` needs no token.

### GitHub Actions constraints

- Repo is public (made public 2026-06-27). GHAS features (CodeQL, SARIF uploads) are now fully available.
- Webhook edits require GitHub sudo re-auth — escalate to Gadget.

## Critical Deadline

**GitHub PAT expires 2027-05-07** — rotate before this date or the entire pipeline goes offline.

## Secrets (GitHub repo secrets)

- `ANTHROPIC_API_KEY` — updated 2026-04-27
- `OPENAI_API_KEY` — updated 2026-03-25
- GitHub PAT — expires 2027-05-07
