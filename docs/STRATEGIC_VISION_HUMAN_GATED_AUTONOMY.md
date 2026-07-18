# Strategic Vision — Human-Gated Autonomy

> Source statement (stress-tested 2026-07-18):
> "Integrating generative, analytical, and workflow tools into an interconnected
> AI ecosystem transforms static, rule-based processes into dynamic,
> self-regulating operations. This agentic approach liberates organizations from
> manual bottlenecks, enabling multi-agent systems to independently plan, utilize
> external software APIs, and execute complex workflows without human intervention."

The direction is correct. The phrase "self-regulating ... without human intervention"
is overclaimed and collapses on contact with our own architecture (see evidence below).
This is the defensible rewrite we ship instead.

---

## Airtight version (use this)

> Integrating generative, analytical, and workflow tooling into one interconnected
> ecosystem turns brittle, rule-based processes into adaptive, observable operations.
> Multi-agent systems plan, call external APIs, and execute complex workflows inside
> **guardrailed envelopes** — every irreversible action is gated by policy, scored for
> risk, and logged for audit. Humans own the edges that cannot be undone (credentials,
> merges, secret rotation); agents own the rest. The result is **human-gated autonomy**:
> the manual bottleneck moves from *doing the task* to *maintaining the system that does
> it* — a smaller, higher-leverage job.

---

## Why the original framing fails (so the rewrite survives a skeptic)

1. **"Without human intervention" is contradicted by our own code.**
   - `dry_run = true` by default (`pyproject.toml` / `config/agent_config.yaml`).
   - `PolicyEngine` gates every destructive GitHub action (`config/policies.yaml`:
     `requires_approval` = delete_main_branch, force_push_protected, modify_secrets,
     merge_to_protected_branch, ...).
   - `RiskScorer` BLOCKS auto-merge at HIGH (6.0–7.9) and BLOCKS + NOTIFIES at
     CRITICAL (8.0–10.0).
   - `AuditLogger` records a forensic trail.
   - Hard credential walls: n8n login, DRC webhook token, GitHub sudo re-auth,
     PAT rotation — none automatable by the agent.
   These are not bugs. They are the product. A truthful vision names them.

2. **"Self-regulating" needs a target function.** Without a defined objective, the
   system optimizes a proxy (PR throughput, "looks done"). We regulate toward *safe,
   reviewed, auditable change* — which is why the gates exist.

3. **Dynamic trades determinism for debuggability.** An agent's decision must be
   reconstructed from logs after it misbehaves. That is the real cost of "dynamic,"
   and it is why we invest in evals/regression harnesses (see `tests/agent_drift_eval.py`).

4. **Blast radius scales with autonomy.** "Independently use external APIs" means one
   bad tool call propagates. Our hedge: local-model routing for LOW-severity tasks,
   cloud only for COMPLEX/CRITICAL, `$1.00/run` cost cap. The hedge is the tell that
   raw autonomy is expensive and dangerous — so we route around it.

## One-line reframe for decks/tweets
"Human-gated autonomy: agents execute inside guardrailed envelopes; humans own the
irreversible edges."
