# Dual Package Layout — Analysis & Decision

**Status:** DECIDED — take no action (Option C). Updated 2026-07-09 after a deeper
investigation corrected the earlier draft of this file.

## The two trees

- **Top-level:** `core/`, `agents/`, `overseer/`, `autopilot/` — the legacy layout.
- **`autonomous_agent/`:** `core/`, `agents/` only — the *installable* package
  (`pyproject.toml` `[project.scripts]`, `setup.py`, CI, `pytest.ini --cov`).

## What the investigation actually found (corrected)

The two trees are **NOT** diverged copies of the same code, and the package is
**NOT** stale or untested. They are *different implementations* with **incompatible
APIs**, and BOTH are exercised by the passing test suite (1339 passed, 2 skipped).

Concrete proof — `core/audit_logger.py` vs `autonomous_agent/core/audit_logger.py`:

| | top-level `core/audit_logger.py` | `autonomous_agent/core/audit_logger.py` |
|---|---|---|
| Style | **async** | **sync** |
| Storage | file + optional Postgres + optional S3 | SQLAlchemy ORM (SQLite/Postgres) + JSON-line mirror |
| Signature | `log_action(agent, action, params, result, task_id)` | `log_action(agent_name, action, repository, details, rollback_instructions)` |
| Features | SHA-256 hash chain, `verify_chain()`, `get_audit_trail()` | `get_logs()`, `get_rollback_instructions()` |
| Lines | 338 | 139 |

`core/github_client.py` vs `autonomous_agent/core/github_client.py` differs by 360
lines with the same async/sync split.

### Blast radius if we forced them to one canonical tree
- **Flat-tree (`core.*`) consumers:** `tests/test_error_recovery.py`,
  `tests/test_github_operations.py`, `tests/test_core.py`,
  `tests/unit/test_github_client.py`, `tests/unit/test_audit_chain.py`,
  `tests/unit/test_audit_logger_extra.py` (7 test files).
- **Package (`autonomous_agent.core.*`) consumers:** `tests/test_audit_logger.py`,
  `tests/test_autonomous_agents.py`, `tests/test_github_client_comprehensive.py`,
  `autonomous_agent/cli.py` (3+ test files + the CLI).
- `test_audit_chain.py` and `test_error_recovery.py` specifically exercise the
  async **hash-chain / tamper-evidence** feature, which the package lacks. A blind
  re-export would break them (`await` on a sync `int`-returning method, missing
  `verify_chain`/`get_audit_trail`).

So "reconcile" is not a merge — it is a 10-file refactor plus, if tamper-evidence
is to be kept, building the hash-chain feature into the ORM logger.

## Decision: Option C — leave both trees as-is (documented debt)

- The suite is **green**; nothing is broken.
- The migration is genuinely *unfinished*, not merely messy — the legacy flat tree
  exists only because tests depend on a feature the package never received.
- Payoff of collapsing the trees (single source of truth) does not justify a
  10-file refactor + possible new feature on a healthy pipeline.

**This corrects the earlier draft of this file**, which wrongly claimed the
package was stale/untested and recommended deleting it (Option B). Deleting the
package would break 5 integration tests and the CLI. That recommendation is
**withdrawn**.

## Guardrails (do NOT silently change one tree and assume the other is fine)
1. Any edit to `core/audit_logger.py` or `core/github_client.py` must keep the
   async hash-chain API intact (it is tested by `test_audit_chain.py` /
   `test_error_recovery.py`).
2. Any edit to `autonomous_agent/core/*` must keep the sync ORM API intact
   (tested by `test_audit_logger.py` / `test_github_client_comprehensive.py` /
   `test_autonomous_agents.py` and used by `cli.py`).
3. The correct time to finish the migration is when audit/GitHub-client code is
   being touched anyway — fold it into that work, not as a standalone risk.

## Future migration paths (only if/when justified)
- **A — package canonical, retire hash-chain:** re-point the 7 flat-tree test files
  + `core/github_client.py` to `autonomous_agent.*`, port or retire
  `test_audit_chain.py`/`test_error_recovery.py`, delete the flat `core/` copies.
  Lower effort; loses tamper-evidence.
- **B — package canonical, port hash-chain in:** implement SHA-256 chain +
  `verify_chain()` + `get_audit_trail()` as a layer on the ORM logger, keep those
  tests, then delete the flat copies. Higher effort; preserves the security feature.
