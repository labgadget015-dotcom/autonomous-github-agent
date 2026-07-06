"""Message formatter: render a Recommendation to the executive-grade template.

Template:
    {emoji} P{n} — {OUTCOME_HEADLINE}
    Blocked by: {prerequisite | none}
    If not done by {DUE_DATE}: {IMPACT}

    1. {one-line step}
    2. ...
    Owner: {@user | unassigned}  Due: {YYYY-MM-DD | TBD}
    Status: {tag}   Ref: {prior_run_id | none}

This replaces the old bot format that buried the subject behind a run_id.
"""

from __future__ import annotations

from recommendation_contract import Recommendation, SEVERITY_EMOJI, validate
from config_loader import get_status_tag

# Fallback tags if config is unavailable; live values come from config.yaml.
_STATUS_TAG_FALLBACK = {
    "open": "🟡 Open",
    "assigned": "🔵 Assigned",
    "inflight": "🟠 In-flight",
    "done": "✅ Done",
    "dropped": "❌ Dropped",
}


def format(r: Recommendation) -> str:
    """Render a validated Recommendation to the Slack message template."""
    ok, errs = validate(r)
    if not ok:
        # Never silently post an invalid recommendation — surface a reject block.
        return _reject_block(r, errs)

    emoji = SEVERITY_EMOJI.get(r.severity, "🟡")
    blocked = f"Blocked by: {r.blocked_by}" if r.blocked_by else "Blocked by: none"
    impact_line = f"If not done by {r.due_date or 'TBD'}: {r.impact_if_ignored}"
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(r.steps, 1))
    owner = r.owner
    due = r.due_date or "TBD"
    status = get_status_tag(r.status) or _STATUS_TAG_FALLBACK.get(r.status, "🟡 Open")
    ref = r.prior_run_id if r.prior_run_id else "none"

    return (
        f"{emoji} {r.severity} — {r.headline}\n"
        f"{blocked}\n"
        f"{impact_line}\n\n"
        f"{steps}\n\n"
        f"Owner: {owner}  Due: {due}\n"
        f"Status: {status}   Ref: {ref}"
    )


def _reject_block(r: Recommendation, errs: list[str]) -> str:
    """Rendered when validate() fails — for the agent log, not Slack."""
    bullets = "\n".join(f"  - {e}" for e in errs)
    return (
        f"⚠️ RECOMMENDATION REJECTED (not posted)\n"
        f"Headline: {r.headline}\n"
        f"Run: {r.run_id or 'n/a'}\n"
        f"Violations:\n{bullets}"
    )
