# DRC Recommendation Contract

Executive-grade message contract + de-dup ledger for the DRC recommendation pipeline.
Directly implements the audit scorecard fixes for `#drc-recommendations`.

> **Status (2026-09-13):** nothing in the repo calls this gate yet — the live DRC
> council runs in n8n. The wiring example below is the intended integration.

## Problem this solves

The DRC bot re-raised "Smoke Test Harness" 5+ times in a week as new P0s, each
without an owner or deadline. Critical items (n8n key expiry) slipped for 8 days
because nothing was named or dated. This module turns the channel from a firehose
into a triage queue.

## Files

```text
autopilot/
├── recommendation_contract.py   # dataclass + validate() (config-driven)
├── message_formatter.py         # render to the new Slack template
├── config_loader.py             # reads config.yaml, stdlib fallback
├── config.yaml                  # recommendation_debounce + status_tags block
├── decisions/
│   └── ledger.py                # append-only ledger, should_post() debounce (file-locked)
└── tests/
    └── test_recommendation_contract.py   # 14 smoke tests (standalone-runnable)

tests/unit/autopilot_recs/       # full suite: schema, exact errors, ledger corruption
```

## The contract

`validate(r)` returns `(ok, errors)` and **never raises**: a wrong-typed field
(e.g. `steps=None`, `headline=None`) is reported as an error, so an emitter loop
can log the reject block and move on.

Every recommendation must carry:

- **severity** — exactly `P0`, `P1` or `P2` (`p0` is rejected, not treated as P2)
- **status** — one of `open`, `assigned`, `inflight`, `done`, `dropped`
- **headline** — the outcome, never a run id; at least 8 characters after
  stripping whitespace (rule toggled by `message_contract.headline_is_outcome`)
- **impact_if_ignored** — required for P0/P1
- **due_date** — required for P0/P1, and when given it must be a real calendar
  date in strict ISO `YYYY-MM-DD` form (`2027-4-30`, `20270430`, `2027-02-30`
  and free text are rejected; surrounding whitespace is ignored)
- **owner** — required for P0; an empty or whitespace-only owner counts as
  `unassigned`, and an unowned P0 is withheld + escalated to `#morning-digest`
- **steps** — a `list` of strings, each **a single line** (no `\n` or `\r`),
  at most `max_step_len` (default 120) characters, with no run id

### Run ids

A run id is `run_` followed by digits, not preceded by a letter, digit or `_`.
So `run_1782796553291`, `(run_42)` and `logs:run_42` are flagged, while
`dry_run_gate.yml`, `rerun_tests` and `run_ directories` are not.

### Signature (de-dup key)

```text
signature = <action_verb>|<target_repo>|<file_or_workflow_path>
```

Each slot is stripped and lower-cased, then escaped:

- `\` becomes `\\` and `|` becomes `\|`, so a field can never forge a slot
  boundary (`a|b` in one field differs from `a` + `b` in two fields)
- **empty slots are kept**, so fields never shift position:
  `("rotate", "", "secrets")` → `rotate||secrets`, which differs from
  `("rotate", "secrets", "")` → `rotate|secrets|`
- if all three slots are blank the signature is `""`, meaning "cannot de-dup":
  `validate()` rejects it and `should_post()` allows it through

**Migration note.** Before 2026-09-13 empty slots were dropped (`rotate|secrets`)
and delimiters were not escaped. Signatures with all three slots filled and no
`|` or `\` are byte-identical in both formats. Any other signature changed — if
a ledger written by the old code exists, rewrite its `sig` values (or accept
that those items will be treated as first raises). No ledger existed when the
format changed.

## Ledger behaviour (`decisions/ledger.py`)

- Appends are serialised with `fcntl.flock` and fsync'd; `seq` counts the
  non-blank lines already in the file.
- **Corrupt lines are skipped, never fatal.** A torn write, undecodable bytes
  or a valid-JSON non-object line (`[1, 2]`, `null`) costs only that line.
- If the previous write was torn (no trailing newline), the next append starts
  a fresh line so it is not glued onto the fragment and lost.
- **Timestamps fail open.** A non-numeric `first_raised_ts`, `transitioned_ts`
  or `seq` (string, `null`, boolean, list) reads as `0`. For debounce that
  means the window looks long elapsed and the item **may repost** — a duplicate
  Slack post is preferred over a crashed recommender. `done`/`dropped` entries
  still never repost, because that rule does not read timestamps.
- The default ledger path is bound at import time from `DECISIONS_LEDGER_PATH`
  (or `config.yaml`); pass `path=` explicitly when the location matters.

## Wiring into the DRC loop

In the recommender, before posting to Slack:

```python
from recommendation_contract import Recommendation, validate
from decisions.ledger import should_post, record
from message_formatter import format

# ...build r: Recommendation from the DRC output...

ok, errs = validate(r)
if not ok:
    log.warning("rejected: %s", errs)
    if r.severity == "P0":
        escalate_to_morning_digest(r)   # unowned P0 -> digest, not #drc-recommendations
    return

allow, reason = should_post(r)
if not allow:
    log.info("suppressed (%s) sig=%s", reason, r.signature())
    return

record(r)                       # append to decision ledger
slack_post("#drc-recommendations", format(r))
```

Executor agents update lifecycle state (not the recommender):

```python
from decisions.ledger import transition
transition(r.signature(), "assigned", owner="U0AKJK1J7GR", due="2026-07-05")
# later: transition(r.signature(), "done")
```

## Run the tests

```bash
python -m pytest tests/unit/autopilot_recs -q          # full suite
python autopilot/tests/test_recommendation_contract.py  # standalone smoke tests
# or: python -m pytest autopilot/tests/ -q
```

## Build order (lowest effort → highest leverage)

1. De-dup + ledger (`ledger.py`) — stops the noise, ~2h, zero risk.
2. Owner/Due enforcement (`recommendation_contract.py`) — plugs the slip.
3. Message reformat (`message_formatter.py`) — restructure the emitter.

## Env

```text
DECISIONS_LEDGER_PATH=autopilot/decisions/recommendations.jsonl   # default if unset
```
