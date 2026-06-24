# GadgetLab Service Inventory

Machine-readable ground truth for GadgetLab infrastructure. Built from verified sources on 2026-06-24.

## Files

| File | Contents |
|------|----------|
| `services.yaml` | All services — n8n workflows, APIs, hosting, local |
| `hosts.yaml` | Compute endpoints — SaaS platforms, homelab, local |
| `networks.yaml` | Traffic flows — ingress, egress, internal, sync |

## How to maintain

1. When a service changes, update `last_verified_at` and the relevant field.
2. Do not leave stale values — mark unknowns as `unknown` rather than removing the field.
3. Add a line to the changelog below when making a structural change.

## Ownership key

| Owner | Meaning |
|-------|---------|
| `platform` | Core pipeline infrastructure — Gadget decides |
| `product` | Landing page / SaaS features |
| `homelab` | Local hardware and VMs |

## Open unknowns (fill these in)

- `tim-postgres` host details — check n8n credential `gndQWH8pCjbtieRf`
- `m900-homelab` IP and OS — SSH or check router
- Tailscale: is it configured? What devices are in the mesh?
- `github-token-expiry-monitor` hardcoded date (2026-05-21) — verify it's still correct
- `iterative-ai-feedback-loop` — activate or archive?

## Changelog

| Date | Change |
|------|--------|
| 2026-06-24 | Initial inventory created from n8n MCP, docker-compose, pyproject, and session memory |
