# Secrets & Token Rotation Runbook

Single source of truth for rotating the credentials that keep the GadgetLab
autonomous agent pipeline alive. If any of these lapse, the pipeline degrades or
goes fully offline.

Last updated: 2026-07-09

## Inventory

| Secret / Token | Where it lives | Expiry | Alert mechanism |
|----------------|---------------|--------|-----------------|
| GitHub PAT (`GITHUB_PAT`) | GitHub repo secret | **2027-05-07** | `.github/workflows/pat-rotation-alert.yml` (monthly, Slack, fails ≤7d) |
| `ANTHROPIC_API_KEY` | GitHub repo secret | — (no hard expiry; rotated 2026-04-27) | none — review every ~6 months |
| `OPENAI_API_KEY` | GitHub repo secret | — (no hard expiry; rotated 2026-03-25) | none — review every ~6 months |
| DRC `x-gadgetlab-token` | **n8n only** (embedded literal in 2 nodes) | Last rotated **2026-07-06** | **none** — see below |
| `SLACK_WEBHOOK_URL` | GitHub repo secret | — | none |

---

## 1. GitHub PAT — rotate before 2027-05-07

**Impact of lapse:** entire CI pipeline stops authenticating → no agent runs, no
overseer, no deploys.

**Automated reminder already exists:** `pat-rotation-alert.yml` runs 09:00 UTC on
the 1st of every month, posts a Slack alert to `#drc-recommendations` once inside
the 90-day window, and *fails the workflow* (red X) when ≤7 days remain. You cannot
miss it without ignoring a failing workflow.

**Manual rotation steps (Gadget only — requires GitHub sudo re-auth):**
1. Go to https://github.com/settings/tokens (or org token admin).
2. Create a new fine-grained or classic PAT with `repo` + `workflow` scopes
   (matches what the workflows need).
3. In the repo → Settings → Secrets and variables → Actions → update `GITHUB_PAT`.
4. Update the `EXPIRY_DATE` constant in `.github/workflows/pat-rotation-alert.yml`
   (line ~16) so the alert counter starts from the new date.
5. Confirm the next scheduled run reports OK.

---

## 2. DRC `x-gadgetlab-token` — NO automated alert (gap to close)

**What it is:** a static shared secret the GitHub Event Router presents in the
`x-gadgetlab-token` header when forwarding to the DRC Agent Loop. The DRC loop's
"Prepare Input" node gates ALL real traffic on it; health-check pings are
short-circuited before the gate (so `n8n-health-check.yml` needs no token).

**Where it lives:** ONLY in n8n, embedded as literals in two nodes:
- Event Router: "Forward to Agent Loop" node (the sole legitimate sender)
- DRC Agent Loop: "Prepare Input" node (the gate)

**Rotation steps (Gadget only — n8n sessions expire after 30–60 min of
inactivity and autosave silently fails with 401; Claude cannot re-auth):**
1. Log into https://gadgetlab.app.n8n.cloud.
2. Open the **GitHub Event Router** workflow → "Forward to Agent Loop" node →
   set the new token value in the header it sends.
3. Open the **DRC Agent Loop** workflow → "Prepare Input" node → set the SAME new
   value in the gate comparison.
4. **Publish both workflows.** (Saving without publishing does nothing.)
5. Verify: hit the loop webhook with the new token — should return the real
   result, not `Unauthorized`. The old value must now be rejected.
6. Update "last rotated" date wherever it's tracked (CLAUDE.md + this file).

**Recommended remediation (TODO, pending your call):**
- Add a `drc-token-rotation-alert.yml` mirroring `pat-rotation-alert.yml` with a
  hardcoded `LAST_ROTATED` date and a 90/30/7-day reminder cadence → Slack.
- Better: move the token out of node literals into an n8n credential / env var so
  rotation is a one-place edit and can be referenced by both nodes. This also
  removes the "embedded literal in two places that must stay in sync" footgun.

---

## 3. LLM API keys (Anthropic / OpenAI)

No hard expiry, but they get rotated by the providers periodically. Current
values: ANTHROPIC (2026-04-27), OPENAI (2026-03-25).

- If a workflow starts 401ing on LLM calls, rotate at the provider console and
  update the repo secret.
- `core/llm_provider.py` abstracts both; no code change needed on rotation.

---

## Pre-expiry reminder (local, optional)

If you want a belt-and-suspenders local nudge (independent of GitHub Actions),
this one-liner prints days remaining until the PAT expires:

    echo $(( ($(date -d 2027-05-07 +%s) - $(date +%s)) / 86400 )) days until PAT expiry

(Replace the date for the DRC token using its last-rotated + your chosen max age.)
