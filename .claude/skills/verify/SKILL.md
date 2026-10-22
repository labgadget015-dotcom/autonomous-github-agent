---
name: verify
description: How to verify changes in this repo at their real surface (mostly GitHub Actions workflows + .github/scripts).
---

# Verifying changes here

Most changes land in `.github/workflows/` + `.github/scripts/`. Surface = Actions runs.

- Merged already? `gh pr view N --json state,mergeCommit`; then read scheduled runs on main:
  `gh run list --workflow <file>.yml --limit 15`.
- `gh run view --log` often returns EMPTY. Use the API instead:
  `gh api repos/labgadget015-dotcom/autonomous-github-agent/actions/jobs/<job_id>/logs`
  and `.../check-runs/<job_id>/annotations` (canary verdicts are `::notice::`/`::error::`).
- Read-only workflows (Intake Canary) are safe to `gh workflow run <file> --ref main`.
- PAID / side-effecting — do NOT dispatch without asking: `drc-e2e-canary.yml` (opens a
  real issue + one DRC council run on LLM spend).

## Canary internals (Neon)
- Workflows read Neon via `secrets.NEON_CANARY_DSN` (`canary_ro`, column-level SELECT).
- Locally, the owner DSN is in `/home/ai/.neon-video-p0` — extract with
  `grep -oE 'postgres(ql)?://[^ "'\'']+'`, never print it, and run with
  `PGOPTIONS='-c default_transaction_read_only=on' psql ...`. No psycopg2 locally; use psql.
- Replay the workflow's exact SQL: awk the `<<'SQL'` heredoc out of the yml, pipe psql output
  into `python3 .github/scripts/intake_canary_neon.py` with `GITHUB_OUTPUT=$(mktemp)`.
