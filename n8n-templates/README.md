# GadgetLab n8n Workflow Templates

Live workflow IDs in gadgetlab.app.n8n.cloud. Import via n8n UI: Settings → Templates, or duplicate directly.

## Core Pipeline

| Workflow | ID | Description |
|----------|----|-------------|
| Dreamer / Realist / Critic — Agent Loop | `Wlfhgk4sUfXJcU4D` | Main DRC pipeline. GitHub webhook → Perplexity research → 3-agent analysis → Postgres + Slack + Drive |
| GitHub Event Router | `oijizIGJtRzBG94Z` | Validates HMAC signatures, filters issues + push events |
| Daily DRC Digest | `shhwyRRdoEdedYLa` | 8 AM daily — reads last 24h from `tim.agent_runs`, Claude summary → Slack + Drive |
| CI Feedback — Slack Alerter | `1QPMbpEuY1MAKMSp` | Webhook `/webhook/ci-feedback` — routes CI pass/fail to `#drc-recommendations` |

## Monitoring

| Workflow | ID | Description |
|----------|----|-------------|
| GitHub Token Expiry — Daily Monitor | `WnqiaE0kYQKSo4I0` | Daily at 09:00 BST — alerts when GitHub PAT (exp 2027-05-07) ≤30 days out |
| n8n API Key — Expiry Monitor | `igKdZJUr5NiUmRei` | Daily at 09:00 BST — alerts when n8n API key (~2026-07-01) ≤14 days out |
| GitHub Token Expiry — Daily Monitor | `WnqiaE0kYQKSo4I0` | Daily check on GitHub PAT rotation deadline |

## Other

| Workflow | ID | Description |
|----------|----|-------------|
| Iterative AI Feedback Loop | `MRLyf7VpwE0Qc8Xp` | Gemini-based feedback loop (credentials needed before live use) |

## Credentials needed for DRC

- **Perplexity API Key** (`I5Z1BiVIUsLHi3Mk`) — assign to "Perplexity Research" node in DRC workflow
- **Google Drive** (`jg6k7UC6E82TJAoy`) — used by Log DRC to Drive node
- **GitHub** (`gkB38oHT6IAyupz8`) — used by Post GitHub Comment + Dispatch Auto-PR
- **Postgres (TIM)** — used by Store to TIM Postgres node

## Webhook endpoints

```
DRC:        https://gadgetlab.app.n8n.cloud/webhook/github-agent-loop
CI Feedback: https://gadgetlab.app.n8n.cloud/webhook/ci-feedback
```
