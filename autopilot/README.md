# DRC Recommendation Contract

Executive-grade message contract + de-dup ledger for the DRC recommendation pipeline.
Directly implements the audit scorecard fixes for `#drc-recommendations`.

## Problem this solves

The DRC bot re-raised "Smoke Test Harness" 5+ times in a week as new P0s, each
without an owner or deadline. Critical items (n8n key expiry) slipped for 8 days
because nothing was named or dated. This module turns the channel from a firehose
into a triage queue.

## Files

```
autopilot/
├── recommendation_contract.py   # dataclass + validate()
├── message_formatter.py         # render to the new Slack template
├── config.yaml                  # recommendation_debounce + status_tags block
├── decisions/
│   └── ledger.py                # append-only ledger, should_post() debounce
└── tests/
    └── test_recommendation_contract.py
```

## The contract

Every recommendation must carry:
- **headline** = the outcome, never a `run_` id
- **impact_if_ignored** (required for P0/P1)
- **due_date** (required for P0/P1)
- **owner** (required for P0; unowned P0 is withheld + escalated to `#morning-digest`)
- **signature** = `action_verb|target_repo|file_or_workflow_path` (for de-dup)

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
python autopilot/tests/test_recommendation_contract.py
# or: python -m pytest autopilot/tests/ -q
```

## Build order (lowest effort → highest leverage)

1. De-dup + ledger (`ledger.py`) — stops the noise, ~2h, zero risk.
2. Owner/Due enforcement (`recommendation_contract.py`) — plugs the slip.
3. Message reformat (`message_formatter.py`) — restructure the emitter.

## Env

```
DECISIONS_LEDGER_PATH=autopilot/decisions/recommendations.jsonl   # default if unset
```
