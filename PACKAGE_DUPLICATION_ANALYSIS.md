# Duplicate Package Layout — Analysis & Recommendation

**Status:** INVESTIGATION ONLY. Nothing has been deleted or moved. This document
records a structural hazard found during the 2026-07-09 maintenance pass and
proposes a fix for your decision.

## Symptom

The repo contains TWO parallel source trees that import the same module names:

- **Top-level:** `core/`, `agents/`, `overseer/`, `autopilot/`
  (the tree the unit tests import — see `tests/unit/test_*.py`)
- **`autonomous_agent/`:** `core/`, `agents/` only — **no `overseer/`, no `autopilot/`**

## Why `autonomous_agent/` exists

It is the *installable* package. It is referenced by:
- `pyproject.toml` → `[project.scripts] autonomous-agent = "autonomous_agent.cli:main"`
  and `[tool.setuptools.packages.find] include = ["autonomous_agent*"]`
- `setup.py` → entry points `autonomous-agent` / `aga`
- `pytest.ini` → `--cov=autonomous_agent` (coverage target that currently shows 0%
  because the top-level tests never exercise it)
- `workflows/ci.yml` → `pytest --cov=autonomous_agent`
- `DEPLOYMENT.md`, install scripts — instruct `import autonomous_agent`

## The hazard

The two trees are **out of sync**, not just duplicated:

| Module | Relationship |
|--------|--------------|
| `core/` | `autonomous_agent/core/` files DIFFER from top-level `core/` files |
| `agents/` | Different files on each side (top has `code_review_agent.py`, `dependency_agent.py`; pkg has `code_reviewer.py`, `branch_manager.py`, etc.) |
| `overseer/` | Only at top level — `autonomous_agent/` has NONE |
| `autopilot/` | Only at top level — `autonomous_agent/` has NONE |

Consequences:
1. Two copies of `core/` that can silently diverge → a fix to one is not a fix to
   the other. A reviewer changing top-level `core/` may believe the package is
   fixed when it is not.
2. `autonomous_agent/` is missing `overseer/` and `autopilot/` entirely, so an
   `import autonomous_agent` install cannot actually run the overseer or autopilot
   — the published package is partially broken vs. the working top-level code.
3. Coverage config (`--cov=autonomous_agent`) measures the wrong tree, hiding the
   real 68% top-level coverage behind a 0% number.

## Recommendation (for your decision — NOT yet applied)

Pick ONE canonical layout and delete the other. Three options:

**Option A — Make `autonomous_agent/` canonical (package-first).**
Move `overseer/` and `autopilot/` into `autonomous_agent/`, delete the top-level
`core/ agents/ overseer/ autopilot/`, and update test imports to use
`autonomous_agent.core` etc. Pros: matches pyproject/setup.py/deployment docs
as-is. Cons: ~40 test files need import rewrites.

**Option B — Make the top-level tree canonical (simplest).**
Delete `autonomous_agent/` and repoint `pyproject.toml`/`setup.py`/`pytest.ini`/
`workflows/ci.yml` to use a top-level package (e.g. add a `src/` layout or just
`[tool.setuptools] py-modules`). Pros: no test rewrites; tests already import this
tree. Cons: needs packaging config edits; `import autonomous_agent` in docs must
change.

**Option C — Keep both but sync via symlink/build step (stopgap).**
Generate `autonomous_agent/` from the top-level tree at build time (e.g. a
`build_package.py` or symlink in CI). Pros: no immediate breakage. Cons: adds
build complexity; doesn't fix the missing `overseer/`/`autopilot/`.

**My recommendation: Option B** — the top-level tree is what actually runs and is
tested (1339 passing tests exercise it). `autonomous_agent/` is stale and
incomplete. Repointing packaging to the working tree is lower-risk than rewriting
40 test imports, and it makes the published package match reality.

## Next step

Confirm A, B, or C and I will execute it (with a full test run to prove no
regression). Until then, treat `autonomous_agent/` as UNTRUSTED — any change to
`core/` should be verified on the top-level tree, not the package copy.
