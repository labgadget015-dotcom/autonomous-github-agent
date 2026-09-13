"""Tests for autopilot/message_formatter.py: golden output, a line-by-line
template schema, the reject block, and the validate()/get_status_tag seams."""

from __future__ import annotations

import re
from unittest import mock

import pytest

from tests.unit.autopilot_recs import _support  # noqa: F401  (sys.path)

# isort: split
import message_formatter  # noqa: E402
from recommendation_contract import SEVERITY_EMOJI, VALID_STATUSES  # noqa: E402

TAGS = {
    "open": "🟡 Open",
    "assigned": "🔵 Assigned",
    "inflight": "🟠 In-flight",
    "done": "✅ Done",
    "dropped": "❌ Dropped",
}
DATE_OR_TBD = r"(\d{4}-\d{2}-\d{2}|TBD)"
TEMPLATE_SCHEMA = [
    r"(🔴|🟠|🟡) P[012] — \S.*",
    r"Blocked by: .+",
    rf"If not done by {DATE_OR_TBD}: .*",
    r"",
    r"1\. \S.*",
    r"2\. \S.*",
    r"3\. \S.*",
    r"",
    rf"Owner: \S+  Due: {DATE_OR_TBD}",
    r"Status: (" + "|".join(map(re.escape, TAGS.values())) + r")   Ref: \S+",
]


# --------------------------------------------------------------------------- #
# golden output
# --------------------------------------------------------------------------- #


def test_golden_full(make_rec):
    rec = make_rec(
        status="assigned",
        blocked_by="PAT admin approval",
        prior_run_id="run_1782796553291",
        run_id="run_1782800000000",
    )
    assert message_formatter.format(rec) == (
        "🔴 P0 — Rotate the GitHub PAT before it expires\n"
        "Blocked by: PAT admin approval\n"
        "If not done by 2027-04-30: Every workflow using the PAT fails and the pipeline goes offline\n"
        "\n"
        "1. Mint a fine-grained PAT with repo + workflow scopes\n"
        "2. Replace the GH_PAT repository secret\n"
        "3. Re-run the canary workflow and confirm it goes green\n"
        "\n"
        "Owner: U0AKJK1J7GR  Due: 2027-04-30\n"
        "Status: 🔵 Assigned   Ref: run_1782796553291"
    )


def test_golden_minimal_p2(make_rec):
    rec = make_rec(
        severity="P2",
        headline="Tidy stale branches",
        impact_if_ignored="",
        due_date="",
        owner="unassigned",
        steps=["Delete merged branches older than 90 days"],
    )
    assert message_formatter.format(rec) == (
        "🟡 P2 — Tidy stale branches\n"
        "Blocked by: none\n"
        "If not done by TBD: \n"  # trailing space: impact is empty
        "\n"
        "1. Delete merged branches older than 90 days\n"
        "\n"
        "Owner: unassigned  Due: TBD\n"
        "Status: 🟡 Open   Ref: none"
    )


def test_golden_zero_steps_leaves_a_double_gap(make_rec):
    out = message_formatter.format(make_rec(steps=[]))
    assert "offline\n\n\n\nOwner: U0AKJK1J7GR" in out


def test_run_id_never_rendered(make_rec):
    out = message_formatter.format(make_rec(run_id="run_1782800000000"))
    assert "run_1782800000000" not in out


# --------------------------------------------------------------------------- #
# template schema
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("status", sorted(VALID_STATUSES))
@pytest.mark.parametrize(
    ("severity", "overrides"),
    [
        ("P0", {}),
        ("P1", {"owner": "unassigned"}),
        ("P2", {"impact_if_ignored": "", "due_date": "", "owner": "unassigned"}),
    ],
    ids=["P0", "P1", "P2"],
)
def test_output_matches_template_schema(make_rec, severity, overrides, status):
    rec = make_rec(severity=severity, status=status, **overrides)
    lines = message_formatter.format(rec).split("\n")
    assert len(lines) == len(TEMPLATE_SCHEMA), lines
    for i, (line, pattern) in enumerate(zip(lines, TEMPLATE_SCHEMA, strict=True)):
        assert re.fullmatch(pattern, line), f"line {i}: {line!r} !~ {pattern!r}"
    assert lines[0].startswith(f"{SEVERITY_EMOJI[severity]} {severity} — ")
    assert lines[-1].startswith(f"Status: {TAGS[status]}   ")


@pytest.mark.parametrize(
    ("status", "tag"),
    list(TAGS.items()),
)
def test_status_tag_line(make_rec, status, tag):
    last = message_formatter.format(make_rec(status=status)).split("\n")[-1]
    assert last == f"Status: {tag}   Ref: none"


@pytest.mark.parametrize(
    "overrides", [{"severity": "P3"}, {"status": "weird"}], ids=["severity", "status"]
)
def test_unknown_severity_or_status_is_rejected_not_rendered(make_rec, overrides):
    out = message_formatter.format(make_rec(**overrides))
    assert out.startswith("⚠️ RECOMMENDATION REJECTED (not posted)\n")


def test_emoji_fallback_only_reachable_past_validate(make_rec):
    with mock.patch.object(message_formatter, "validate", return_value=(True, [])):
        out = message_formatter.format(make_rec(severity="P3"))
    assert out.split("\n")[0] == "🟡 P3 — Rotate the GitHub PAT before it expires"


@pytest.mark.parametrize(
    ("overrides", "violation"),
    [
        ({"steps": None}, "steps must be a list of strings, got NoneType"),
        ({"headline": None}, "headline must be a string, got NoneType"),
    ],
    ids=["steps-none", "headline-none"],
)
def test_malformed_recommendation_yields_reject_block_not_exception(
    make_rec, overrides, violation
):
    out = message_formatter.format(make_rec(**overrides))
    assert out.startswith("⚠️ RECOMMENDATION REJECTED (not posted)\n")
    assert out.endswith(f"Violations:\n  - {violation}")


# --------------------------------------------------------------------------- #
# config-driven status tags
# --------------------------------------------------------------------------- #


def test_config_tag_override(write_config, make_rec):
    write_config("status_tags:\n  done: 'SHIPPED'\n")
    assert message_formatter.format(make_rec(status="done")).endswith(
        "Status: SHIPPED   Ref: none"
    )


def test_empty_config_tag_uses_module_fallback(write_config, make_rec):
    # The only path that reaches _STATUS_TAG_FALLBACK: get_status_tag() returns "".
    write_config("status_tags:\n  inflight: ''\n")
    out = message_formatter.format(make_rec(status="inflight"))
    assert out.endswith("Status: 🟠 In-flight   Ref: none")


def test_fallback_table_matches_config_defaults():
    import config_loader

    assert (
        message_formatter._STATUS_TAG_FALLBACK
        == config_loader.DEFAULTS["status_tags"]
        == TAGS
    )


# --------------------------------------------------------------------------- #
# reject block
# --------------------------------------------------------------------------- #


def test_reject_block_golden(make_rec):
    rec = make_rec(owner="unassigned", run_id="run_1782800000000")
    assert message_formatter.format(rec) == (
        "⚠️ RECOMMENDATION REJECTED (not posted)\n"
        "Headline: Rotate the GitHub PAT before it expires\n"
        "Run: run_1782800000000\n"
        "Violations:\n"
        "  - P0 with no owner — withhold, escalate to #morning-digest"
    )


def test_reject_block_lists_every_violation_in_order(make_rec):
    rec = make_rec(impact_if_ignored="", due_date="", steps=["x" * 121])
    assert message_formatter.format(rec) == (
        "⚠️ RECOMMENDATION REJECTED (not posted)\n"
        "Headline: Rotate the GitHub PAT before it expires\n"
        "Run: n/a\n"
        "Violations:\n"
        "  - P0 missing impact_if_ignored\n"
        "  - P0 missing due_date\n"
        "  - step 1 > 120 chars (split it)"
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"owner": "unassigned"},
        {"headline": "run_1782796553291"},
        {"steps": ["see run_42"]},
        {"action_verb": "", "target_repo": "", "file_or_workflow_path": ""},
    ],
    ids=["no-owner", "run-id-headline", "run-id-step", "no-signature"],
)
def test_invalid_never_renders_the_slack_template(make_rec, overrides):
    out = message_formatter.format(make_rec(**overrides))
    assert out.startswith("⚠️ RECOMMENDATION REJECTED (not posted)\n")
    assert not re.search(r"^(Owner|Status|Blocked by): ", out, flags=re.MULTILINE)


# --------------------------------------------------------------------------- #
# collaborator seams
# --------------------------------------------------------------------------- #


def test_format_defers_entirely_to_validate_on_reject(make_rec):
    rec = make_rec()
    with mock.patch.object(
        message_formatter, "validate", return_value=(False, ["forced"])
    ) as v:
        out = message_formatter.format(rec)
    v.assert_called_once_with(rec)
    assert out.endswith("Violations:\n  - forced")


def test_format_trusts_validate_on_accept(make_rec):
    rec = make_rec(owner="unassigned")  # invalid by the real rules
    with mock.patch.object(message_formatter, "validate", return_value=(True, [])):
        out = message_formatter.format(rec)
    assert "Owner: unassigned  Due: 2027-04-30" in out


def test_format_asks_config_for_the_status_tag(make_rec):
    with mock.patch.object(
        message_formatter, "get_status_tag", return_value="TAG"
    ) as tag:
        out = message_formatter.format(make_rec(status="inflight"))
    tag.assert_called_once_with("inflight")
    assert out.endswith("Status: TAG   Ref: none")
