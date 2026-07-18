# Human-in-the-Loop Protocol — The One-Step Intervention Rule

Principle (from strategy work 2026-07-18): autonomy trades manual toil for
orchestration debt. The human is not removed — they are moved to the irreversible
edges (credentials, merges, secret rotation). Every time the system hits a guard,
the interaction must cost Gadget **one trivial step**, not a context-switch.

## The rule
When any guard trips, the agent MUST pre-do everything on its side, then hand off a
single copy-paste action (or one QR scan). Never present a multi-step manual procedure.

## Guard → one-step handoff matrix

| Guard trips because… | What the agent pre-does | The one step Gadget runs |
|---|---|---|
| RiskScorer = HIGH/CRITICAL | Stages fix, runs ruff+pytest, writes the evidence block | `gh pr merge <N> --squash` (or "approve in UI") |
| n8n session expired (401) | Identifies exact node + field to edit, drafts new value | Log in to gadgetlab.app.n8n.cloud, open node, paste |
| DRC `x-gadgetlab-token` rotation | Computes new token, writes it as a string for both nodes | Paste into both nodes' literals, click Publish x2 |
| GitHub sudo re-auth needed (webhook edit) | Prepares the exact webhook payload/diff | Re-auth when GitHub prompts |
| PAT rotation (by 2027-05-07) | Generates the new PAT scope list + rotation checklist | Paste new PAT into repo secret, click Save |
| Cron delivery channel missing | Pairs the bot, verifies `hermes status` = configured | Send ONE message to the bot to register the chat |

## Standing UX constraints (verified working patterns)
- Telegram delivery: pin the chat id, never rely on discovery.
  `deliver='telegram:8834644752'` (confirmed ✓ configured 2026-07-18).
  Bare `deliver='telegram'` silently fails ("no delivery target resolved").
- When the handoff is a command, print it as one fenced block, no preamble prose.
- When the handoff is a QR/OAuth, do everything else first so the human only scans.

## Anti-patterns (do NOT do these)
- "Go to settings, find the secret, rotate it, update the workflow, re-run CI."
- Asking Gadget to debug a failure the agent could have reproduced locally first.
- Shipping a cron with `deliver='slack'` when Slack is unauthenticated (it schedules
  fine, then fails silently at fire time).
