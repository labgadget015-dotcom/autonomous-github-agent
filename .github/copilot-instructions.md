# GitHub Copilot Instructions — Autonomous GitHub Agent

## Project overview

This repo is the **GadgetLab Autonomous GitHub Agent** — a three-layer pipeline that automatically analyses GitHub issues and PRs using a Dreamer-Realist-Critic (DRC) multi-agent pattern.

**Stack:**
- Python 3.10–3.12 (core agents, overseer, autopilot)
- n8n cloud (workflow orchestration — gadgetlab.app.n8n.cloud)
- Anthropic Claude Sonnet (claude-sonnet-4-6) — three AI agent nodes
- GitHub Actions (12 workflows in .github/workflows/)
- Next.js 14 + Tailwind CSS (landing page in landing/)
- Stripe (subscription billing for Growth tier at $199/mo)
- Postgres via TIM (agent_runs table, llm_cache table)

## Architecture

```
GitHub webhook
  → n8n: GitHub Event Router (HMAC validation + event filtering)
  → n8n: DRC Agent Loop (DREAMER → REALIST → CRITIC)
  → GitHub comment on issue + Slack #drc-recommendations
  → Store to TIM Postgres (tim.agent_runs)
```

## Python conventions

- All agents extend `core/agent_base.py:BaseAgent` — lifecycle: validate → policy check → execute → audit log
- Use `core/llm_provider.py` for all LLM calls — never call Anthropic/OpenAI directly
- Risk scoring: `core/risk_scorer.py` — bands: 0–2.9 LOW, 3–5.9 MEDIUM, 6–7.9 HIGH, 8–10 CRITICAL
- Policy enforcement: `core/policy_engine.py` checks `config/policies.yaml` before any write
- Dry-run is ON by default — always check `dry_run` flag before executing destructive actions
- No inline comments unless the WHY is non-obvious
- Type hints on all public functions
- Tests go in `tests/unit/` for unit tests, `tests/` root for integration tests

## Landing page (landing/)

- Next.js 14 App Router — all routes under `landing/app/`
- Tailwind CSS for styling — brand colour is blue (`brand-600: #2563eb`)
- Stripe Payment Link (not Checkout Session) for Growth tier — zero backend required for MVP
- Stripe webhook handler at `landing/app/api/stripe/webhook/route.ts`
- Environment variables documented in `landing/.env.example`
- Deploy target: Vercel (via `.github/workflows/deploy-landing.yml`)

## Stripe integration

- Growth tier: $199/month (Price ID to be created in Stripe dashboard)
- Enterprise tier: $2,499/month (contact sales — no self-serve checkout)
- Webhook events to handle: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
- After checkout: notify n8n via `N8N_STRIPE_WEBHOOK_URL` env var for downstream automation

## GitHub Actions

- All secrets referenced as `${{ secrets.SECRET_NAME }}`
- All repo-level variables as `${{ vars.VAR_NAME }}`
- Required secrets for landing deploy: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_GROWTH_PAYMENT_LINK`
- SARIF uploads always use `continue-on-error: true` (repo is private, no GHAS)

## Things to avoid

- Never commit secrets or API keys
- Never add `resource: "document"` to n8n Anthropic LangChain nodes (breaks execution)
- Never use `$vars.` in n8n expressions (requires Pro plan, not available)
- Don't add error handling for scenarios that can't happen
- Don't add abstractions beyond what the task requires
