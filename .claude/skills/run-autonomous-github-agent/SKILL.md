---
name: run-autonomous-github-agent
description: Set up, run, and drive autonomous-github-agent locally - the autonomous_agent CLI, the MCP server (mcp_server/server.py) over real stdio, the core risk scorer, .github/scripts, run_overseer.py, the autopilot daily summary, and the pytest suite. Use when asked to run/start/test/smoke this repo, call an MCP tool, score a PR's risk, or confirm a change works outside CI.
---

Python repo with several entry points and no long-running server. Drive it all through
**`.claude/skills/run-autonomous-github-agent/driver.sh`**, which owns the three things that
break a naive run: the venv, the cwd, and the env. All paths are relative to the repo root.

For checking **GitHub Actions runs** and the Neon canaries, use the local `/verify` skill if
it is present (`.claude/skills/verify/`; untracked, host-specific).

## Setup (once, ~5 s with uv)

Needs `uv` (`~/.local/bin/uv`), plus `gh` logged in for anything that touches GitHub.

```bash
.claude/skills/run-autonomous-github-agent/driver.sh setup
```

This creates a Python 3.11 venv (the CI's primary version) at `~/.venvs/autonomous-github-agent`
(`AGA_VENV` overrides it), outside the repo on purpose. It installs `requirements.txt`, the
pytest plugins, and `mcp<2`. The setup command is idempotent.

## Run (agent path)

```bash
D=.claude/skills/run-autonomous-github-agent/driver.sh

# Test suite (CI-like, with coverage; ~37 s, 1815 passed / 2 skipped, gate 70%)
$D test -q -n 4
$D test tests/unit/test_intake_canary_neon.py -q --no-cov   # one file
$D test -q --no-cov -k risk                                 # filter

# core/ direct invocation: risk scorer -> markdown + band line
$D risk '{"files_changed":3,"additions":120,"deletions":10,"changed_paths":[".github/workflows/ci.yml","core/policy_engine.py","README.md"]}'

# MCP server over real stdio (spawns mcp_server/server.py; DRY_RUN=true unless exported)
$D mcp list
$D mcp call score_pr '{"files_changed":3,"additions":120,"deletions":10,"changed_paths":["core/policy_engine.py"]}'
$D mcp call get_pull_request '{"repo":"labgadget015-dotcom/autonomous-github-agent","pr_number":344}'

# CLI (read-only GitHub calls; ~20 s for analyze)
$D cli config-check
$D cli analyze --repo labgadget015-dotcom/autonomous-github-agent --agent health
$D cli logs --limit 3

# .github/scripts: run any of them with the venv python. Canary example, healthy -> exit 0:
echo '{"now":"2026-10-08T09:00:00+00:00","latest_at":"2026-10-08T07:40:00+00:00","forwarded":3,"unmatched":[]}' \
  | GITHUB_OUTPUT=/tmp/aga-work/gh_output $D script intake_canary_neon.py

# Overseer, code analysis only (~2 s, writes $AGA_WORK/overseer-results.json, no repo changes)
$D overseer --only code

# Autopilot daily summary (~17 s, scans the 4 repos in autopilot/config.yaml,
# writes $AGA_WORK/DAILY_SUMMARY.md)
$D autopilot
```

`AGA_WORK` (default `/tmp/aga-work`) is the clean cwd. CLI `logs/audit.db`, coverage `htmlcov/`, overseer
output and the autopilot summary all land there. `GITHUB_TOKEN` defaults to `gh auth token`.

**Not exercised; ask the user first.** The MCP write tools (`create_issue`, `add_comment`,
`add_labels`, `merge_pull_request`, `trigger_drc_agent`) and the CLI's `review` / `monitor`.
Dry-run is only the *default*: any caller can pass `"dry_run": false` per call.
`script`/`overseer`/`cli` export a real `gh` token with repo and workflow scope. Only
`intake_canary_neon.py` and `overseer --only code` were exercised. Several scripts write to
GitHub (`auto_pr.py`, `issue_auto_creator.py`, `pr_inline_commenter.py`, `release_manager.py`,
`setup_branch_protection.py`), and the other overseer modes may write files. Read anything
else before running it.

## Run (human path)

`python -m autonomous_agent.cli <cmd>` from the repo root is what README/HOW_TO_RUN.md show.
**It fails here**; see `.env` in Gotchas. Use `$D cli`.

## Gotchas

- **The repo's `.venv` is broken.** `bin/python` symlinks to `/usr/bin/python3`, which is now
  3.14 with no project deps. Its cfg says 3.12 and system site-packages, so you get
  `No module named 'pydantic'`. Don't `rm -rf` it (the repo CLAUDE.md forbids it). The driver
  uses its own venv instead.
- **Keep any venv out of the repo tree unless it's named `.venv`/`venv`.**
  `overseer/code_analyzer.py` excludes only those names. A `.venv-run/` inside the repo made
  `overseer --only code` scan site-packages: 427k "refactoring opportunities" and 2 minutes,
  instead of 4.4k and 2 s.
- **The placeholder `.env` in the repo root breaks pydantic-settings.** `Config` reads `./.env`
  (relative to the **cwd**) and forbids extra keys. Its `GITHUB_TOKEN=`/`LLM_*` lines cause
  `8 validation errors for Config ... extra_forbidden`, which fails the CLI and the suite
  (from the repo root: 9 failed, 43 errors). CI has no `.env`. That's why the driver always `cd`s to `$AGA_WORK`.
  The traceback **echoes the .env values**. They're placeholders today; if someone fills in
  real ones, that error prints secrets.
- `GITHUB_TOKEN` in `.env` is **never read** anyway: the nested `GitHubSettings` only reads
  real env vars. Export it (the driver does).
- `autopilot/autopilot.py` calls `load_dotenv()`, which searches upward from the *script's*
  dir, so it always finds the placeholder `.env`. That's harmless only because it doesn't
  override variables that are already exported. Run it without `GITHUB_TOKEN` exported and it
  uses `ghp_your_github_...`.
- **`cli health-check` is a stub.** It returns hard-coded `github_connection: ok,
  llm_connection: ok` without touching the network. For a real check use
  `cli analyze --agent health`.
- **`cli analyze --agent` accepts only `health` or `security`.** The names `list-agents` prints
  (`health_monitor`, ...) match nothing, print no output, and still say `✓ Analysis complete!`
  with exit 0.
- `LLMClient()` builds an OpenAI client eagerly, so every command that isn't LLM-related needs
  `LLM_API_KEY`. The driver sets `dummy-not-used`, which makes `config-check` show
  `LLM API Key ✓ Set`. That's the dummy, not a real key.
- **Unpinned `mcp` installs 2.x**, which removed `mcp.server.fastmcp`. The server dies on
  import and the client only sees `MCPError: Connection closed`. Pin `mcp<2` (it isn't in
  requirements.txt at all).
- **MCP `check_rate_limit` is broken** on current PyGithub:
  `'RateLimitOverview' object has no attribute 'core'` (`core/github_client.py:84`; it should
  be `.resources.core`).
- **MCP `trigger_drc_agent` hardcodes the legacy Cloud webhook**
  (`mcp_server/server.py` `_N8N_DRC_WEBHOOK`). The Cloud DRC was unpublished 2026-10-04, and
  the tool sends no `x-gadgetlab-token`. With dry-run off it hits a dead endpoint; pointed at
  the M900 it would cost real LLM money.
- **Risk band ≠ auto-merge gate.** `blocks_auto_merge` is true only for HIGH/CRITICAL. A MEDIUM
  5.5 PR prints `✅ Eligible for auto-merge`, even though docs say MEDIUM "needs review".
- `overseer --only code` reports `Quality Score: 0/100` on this repo. That's its real output,
  not an environment problem. `actions_taken` stays `[]`.
- `pytest` from inside `$AGA_WORK` needs `-c pytest.ini --rootdir=<repo>` plus absolute test
  paths, or it collects nothing (`no tests ran`). The driver rewrites `tests/...` args for you.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'pydantic'` | You used the repo `.venv`. Run `$D setup`, then `$D ...` |
| `ValidationError: 8 validation errors for Config ... extra_forbidden` | You ran from the repo root (`.env`). Use `$D cli` / `$D test` |
| `ValidationError ... GitHubSettings token Field required` | `GITHUB_TOKEN` unset and `gh` not logged in |
| `openai.OpenAIError: Missing credentials` | `LLM_API_KEY` unset (the driver defaults it) |
| `No module named 'mcp.server.fastmcp' ... This is mcp 2.x` | `uv pip install --python ~/.venvs/autonomous-github-agent/bin/python 'mcp<2'` |
| `no tests ran` | Test path not absolute from the clean cwd. Pass `tests/...` through `$D test` |
