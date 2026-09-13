"""Tests for autopilot/recommendation_contract.py.

Three layers: the dataclass/Literal schema, validate()'s exact error output,
and an AST check that validate() reads exactly the config keys it should.

The "hardened rules" section pins contract gaps fixed on 2026-09-13; they were
strict-xfail KNOWN GAP tests until the source was corrected.
"""

from __future__ import annotations

import ast
import dataclasses
import typing
from pathlib import Path

import pytest

from tests.unit.autopilot_recs import _support  # noqa: F401  (sys.path)

# isort: split
import config_loader  # noqa: E402
import recommendation_contract as rc  # noqa: E402
from recommendation_contract import Recommendation, validate  # noqa: E402

H = "headline must be an outcome, not a run_id"
P0_OWNER = "P0 with no owner — withhold, escalate to #morning-digest"
SIG_ERR = "missing signature fields (action_verb + target + path)"
MISSING = dataclasses.MISSING


# --------------------------------------------------------------------------- #
# schema
# --------------------------------------------------------------------------- #


def test_dataclass_schema_is_exact():
    expected = [
        ("severity", "Severity", MISSING),
        ("headline", "str", MISSING),
        ("impact_if_ignored", "str", MISSING),
        ("steps", "list[str]", MISSING),
        ("due_date", "str", MISSING),
        ("owner", "str", "unassigned"),
        ("status", "Status", "open"),
        ("blocked_by", "str", ""),
        ("target_repo", "str", ""),
        ("file_or_workflow_path", "str", ""),
        ("action_verb", "str", ""),
        ("prior_run_id", "str", ""),
        ("run_id", "str", ""),
    ]
    actual = [(f.name, f.type, f.default) for f in dataclasses.fields(Recommendation)]
    assert actual == expected
    assert all(f.default_factory is MISSING for f in dataclasses.fields(Recommendation))


def test_required_fields_are_enforced_by_constructor():
    with pytest.raises(TypeError, match="due_date"):
        Recommendation(
            severity="P0", headline="h" * 10, impact_if_ignored="i", steps=[]
        )


def test_literal_types_and_lookup_tables_agree():
    assert typing.get_args(rc.Severity) == ("P0", "P1", "P2")
    assert typing.get_args(rc.Status) == (
        "open",
        "assigned",
        "inflight",
        "done",
        "dropped",
    )
    assert rc.VALID_STATUSES == set(typing.get_args(rc.Status))
    assert rc.SEVERITY_EMOJI == {"P0": "🔴", "P1": "🟠", "P2": "🟡"}
    assert set(rc.SEVERITY_EMOJI) == set(typing.get_args(rc.Severity))
    assert set(config_loader.DEFAULTS["status_tags"]) == rc.VALID_STATUSES
    assert (
        set(config_loader.DEFAULTS["recommendation_debounce"]["repost_policy"])
        == rc.VALID_STATUSES
    )
    assert rc.RUN_ID_TOKEN == "run_"


# --------------------------------------------------------------------------- #
# AST: validate() <-> message_contract config keys
# --------------------------------------------------------------------------- #


def _contract_gets() -> dict[str, object]:
    """Map each ``contract.get(<key>, <fallback>)`` in validate() to its fallback."""
    tree = ast.parse(Path(rc.__file__).read_text(encoding="utf-8"))
    fn = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate"
    )
    out: dict[str, object] = {}
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "contract"
        ):
            key = ast.literal_eval(node.args[0])
            fallback = node.args[1]
            out[key] = (
                getattr(rc, fallback.id)
                if isinstance(fallback, ast.Name)
                else ast.literal_eval(fallback)
            )
    return out


def test_validate_reads_exactly_the_expected_contract_keys():
    read = set(_contract_gets())
    declared = set(config_loader.DEFAULTS["message_contract"])
    assert read == {
        "max_step_len",
        "headline_is_outcome",
        "require_impact_for",
        "require_due_for",
        "require_owner_for",
    }
    # Every key declared in config.yaml + DEFAULTS is honoured.
    assert declared == read


def test_validate_inline_fallbacks_match_config_defaults():
    defaults = config_loader.DEFAULTS["message_contract"]
    for key, fallback in _contract_gets().items():
        assert fallback == defaults[key], key


# --------------------------------------------------------------------------- #
# signature()
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("verb", "repo", "path", "expected"),
    [
        ("create", "repo", "path", "create|repo|path"),
        (
            "  Create ",
            "REPO",
            " .GitHub/Workflows/X.yml ",
            "create|repo|.github/workflows/x.yml",
        ),
        ("create", "", "", "create||"),
        ("", "repo", "", "|repo|"),
        ("", "", "path", "||path"),
        ("", "", "", ""),
        (" ", "\t", "\n", ""),
        ("create", "a|b", "c", "create|a\\|b|c"),
        ("create", "a\\", "|c", "create|a\\\\|\\|c"),
    ],
    ids=[
        "plain",
        "normalised",
        "verb-only",
        "repo-only",
        "path-only",
        "all-empty",
        "all-whitespace",
        "pipe-escaped",
        "backslash-escaped",
    ],
)
def test_signature(make_rec, verb, repo, path, expected):
    rec = make_rec(action_verb=verb, target_repo=repo, file_or_workflow_path=path)
    assert rec.signature() == expected


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (("rotate", "", "secrets"), ("rotate", "secrets", "")),
        (("a|b", "", ""), ("a", "b", "")),
        (("a\\", "b", ""), ("a\\|b", "", "")),
    ],
    ids=["slot-shift", "pipe-forgery", "backslash-forgery"],
)
def test_distinct_work_items_never_share_a_signature(make_rec, a, b):
    ra = make_rec(action_verb=a[0], target_repo=a[1], file_or_workflow_path=a[2])
    rb = make_rec(action_verb=b[0], target_repo=b[1], file_or_workflow_path=b[2])
    assert ra.signature() != rb.signature()


@pytest.mark.parametrize(
    "fields",
    [
        ("create", "autonomous-github-agent", ".github/workflows/smoke-test.yml"),
        ("  Rotate ", "Repo", "Secrets/PAT"),
        ("configure", "org/repo", "config/policies.yaml"),
    ],
)
def test_signature_unchanged_when_every_slot_is_filled(make_rec, fields):
    # Pre-hardening formula: fully-populated, pipe-free signatures stay byte-identical.
    legacy = "|".join(p.strip().lower() for p in fields if p.strip())
    rec = make_rec(
        action_verb=fields[0], target_repo=fields[1], file_or_workflow_path=fields[2]
    )
    assert rec.signature() == legacy


# --------------------------------------------------------------------------- #
# validate(): exact output
# --------------------------------------------------------------------------- #


def test_valid_recommendation(make_rec):
    assert validate(make_rec()) == (True, [])


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"headline": "run_1782796553291"}, [H]),
        ({"headline": "   run_1782796553291 retry"}, [H]),
        ({"headline": "Fix CI"}, [H]),
        ({"headline": "x" * 7}, [H]),
        ({"headline": "x" * 8}, []),
        ({"impact_if_ignored": ""}, ["P0 missing impact_if_ignored"]),
        ({"impact_if_ignored": " \t\n"}, ["P0 missing impact_if_ignored"]),
        ({"due_date": ""}, ["P0 missing due_date"]),
        ({"due_date": "   "}, ["P0 missing due_date"]),
        ({"owner": "unassigned"}, [P0_OWNER]),
        ({"steps": [""]}, ["step 1 empty"]),
        ({"steps": ["ok step", "   "]}, ["step 2 empty"]),
        ({"steps": ["x" * 120]}, []),
        ({"steps": ["ok", "x" * 121]}, ["step 2 > 120 chars (split it)"]),
        (
            {"steps": ["see run_123 for logs"]},
            ["step 1 contains run_id (move to Ref: footer)"],
        ),
        (
            {"steps": ["run_1" + "x" * 120]},
            [
                "step 1 > 120 chars (split it)",
                "step 1 contains run_id (move to Ref: footer)",
            ],
        ),
        ({"steps": []}, []),
        (
            {"action_verb": "", "target_repo": "", "file_or_workflow_path": ""},
            [SIG_ERR],
        ),
        (
            {"action_verb": " ", "target_repo": "\t", "file_or_workflow_path": "\n"},
            [SIG_ERR],
        ),
        (
            {
                "headline": "run_1",
                "impact_if_ignored": "",
                "due_date": "",
                "owner": "unassigned",
                "steps": ["", "run_2"],
                "action_verb": "",
                "target_repo": "",
                "file_or_workflow_path": "",
            },
            [
                H,
                "P0 missing impact_if_ignored",
                "P0 missing due_date",
                P0_OWNER,
                "step 1 empty",
                "step 2 contains run_id (move to Ref: footer)",
                SIG_ERR,
            ],
        ),
    ],
    ids=[
        "headline-run-id",
        "headline-run-id-padded",
        "headline-short",
        "headline-7",
        "headline-8-boundary-ok",
        "impact-empty",
        "impact-whitespace",
        "due-empty",
        "due-whitespace",
        "owner-unassigned",
        "step-empty",
        "step-whitespace",
        "step-120-boundary-ok",
        "step-121",
        "step-run-id",
        "step-long-and-run-id",
        "no-steps-ok",
        "no-signature",
        "whitespace-signature",
        "everything-wrong-ordered",
    ],
)
def test_validate_exact_errors_p0(make_rec, overrides, expected):
    ok, errs = validate(make_rec(**overrides))
    assert errs == expected
    assert ok is (expected == [])


@pytest.mark.parametrize(
    ("severity", "overrides", "expected"),
    [
        ("P1", {"owner": "unassigned"}, []),
        ("P1", {"impact_if_ignored": ""}, ["P1 missing impact_if_ignored"]),
        ("P1", {"due_date": ""}, ["P1 missing due_date"]),
        ("P2", {"impact_if_ignored": "", "due_date": "", "owner": "unassigned"}, []),
        ("P2", {"headline": "run_1782796553291"}, [H]),
        ("P2", {"steps": ["x" * 121]}, ["step 1 > 120 chars (split it)"]),
    ],
    ids=[
        "p1-no-owner-ok",
        "p1-no-impact",
        "p1-no-due",
        "p2-relaxed",
        "p2-headline-rule",
        "p2-step-rule",
    ],
)
def test_validate_severity_rules(make_rec, severity, overrides, expected):
    assert validate(make_rec(severity=severity, **overrides)) == (
        expected == [],
        expected,
    )


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"headline": None}, ["headline must be a string, got NoneType"]),
        (
            {"impact_if_ignored": None},
            ["impact_if_ignored must be a string, got NoneType"],
        ),
        ({"due_date": None}, ["due_date must be a string, got NoneType"]),
        ({"owner": 42}, ["owner must be a string, got int"]),
        ({"steps": None}, ["steps must be a list of strings, got NoneType"]),
        ({"steps": "Rotate-the-PAT"}, ["steps must be a list of strings, got str"]),
        ({"steps": ("a step",)}, ["steps must be a list of strings, got tuple"]),
        (
            {"steps": ["ok", None, 123]},
            [
                "step 2 must be a string, got NoneType",
                "step 3 must be a string, got int",
            ],
        ),
        (
            {"action_verb": None, "run_id": 7},
            [
                "action_verb must be a string, got NoneType",
                "run_id must be a string, got int",
            ],
        ),
    ],
    ids=[
        "headline-none",
        "impact-none",
        "due-none",
        "owner-int",
        "steps-none",
        "steps-str",
        "steps-tuple",
        "step-elements",
        "field-order",
    ],
)
def test_validate_reports_wrong_types_without_raising(make_rec, overrides, expected):
    assert validate(make_rec(**overrides)) == (False, expected)


# --------------------------------------------------------------------------- #
# validate(): config-driven rules
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("contract_yaml", "severity", "overrides", "expected"),
    [
        ("max_step_len: 20", "P0", {"steps": ["x" * 20]}, []),
        (
            "max_step_len: 20",
            "P0",
            {"steps": ["x" * 21]},
            ["step 1 > 20 chars (split it)"],
        ),
        ("require_impact_for: []", "P0", {"impact_if_ignored": ""}, []),
        ("require_due_for: ['P2']", "P2", {"due_date": ""}, ["P2 missing due_date"]),
        ("require_due_for: ['P2']", "P0", {"due_date": ""}, []),
        # The message names the severity that triggered the rule.
        (
            "require_owner_for: ['P0', 'P1']",
            "P1",
            {"owner": "unassigned"},
            ["P1 with no owner — withhold, escalate to #morning-digest"],
        ),
        ("headline_is_outcome: false", "P0", {"headline": "run_1782796553291"}, []),
        ("headline_is_outcome: true", "P0", {"headline": "run_1782796553291"}, [H]),
    ],
    ids=[
        "step-len-boundary",
        "step-len-over",
        "impact-not-required",
        "due-required-for-p2",
        "due-not-required-for-p0",
        "owner-for-p1-labelled",
        "headline-flag-off-disables-rule",
        "headline-flag-on",
    ],
)
def test_validate_honours_config(
    write_config, make_rec, contract_yaml, severity, overrides, expected
):
    write_config(f"message_contract:\n  {contract_yaml}\n")
    assert validate(make_rec(severity=severity, **overrides)) == (
        expected == [],
        expected,
    )


def test_validate_uses_inline_fallbacks_for_an_empty_contract(monkeypatch, make_rec):
    monkeypatch.setattr(config_loader, "get_contract", lambda: {})
    assert validate(make_rec(steps=["x" * 121], owner="unassigned")) == (
        False,
        [P0_OWNER, "step 1 > 120 chars (split it)"],
    )


def test_validate_crashes_on_null_contract_section(write_config, make_rec):
    write_config("message_contract: null\n")
    with pytest.raises(AttributeError):
        validate(make_rec())


# --------------------------------------------------------------------------- #
# hardened rules (formerly strict-xfail KNOWN GAPs)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("owner", ["", "   "], ids=["empty", "whitespace"])
def test_p0_blank_owner_is_rejected(make_rec, owner):
    assert validate(make_rec(owner=owner)) == (False, [P0_OWNER])


@pytest.mark.parametrize(
    "headline", [" " * 8, "  short  "], ids=["all-spaces", "padded-short"]
)
def test_headline_length_is_measured_after_strip(make_rec, headline):
    assert validate(make_rec(headline=headline)) == (False, [H])


@pytest.mark.parametrize(
    "severity", ["p0", "P3", ""], ids=["lowercase-p0", "p3", "empty"]
)
def test_unknown_severity_is_rejected(make_rec, severity):
    # Previously "p0" with no owner/impact/due sailed through every P0 rule.
    rec = make_rec(
        severity=severity, owner="unassigned", impact_if_ignored="", due_date=""
    )
    assert validate(rec) == (
        False,
        [f"unknown severity {severity!r}; expected one of ['P0', 'P1', 'P2']"],
    )


def test_unknown_status_is_rejected(make_rec):
    assert validate(make_rec(status="assiged")) == (
        False,
        [
            "unknown status 'assiged'; expected one of ['assigned', 'done', 'dropped', 'inflight', 'open']"
        ],
    )


@pytest.mark.parametrize(
    "step",
    ["Rotate the token\nthen redeploy", "Rotate\r\nredeploy", "Rotate the token\n"],
    ids=["lf", "crlf", "trailing-newline"],
)
def test_multiline_step_is_rejected(make_rec, step):
    assert validate(make_rec(steps=[step])) == (
        False,
        ["step 1 spans multiple lines (one line per step)"],
    )


@pytest.mark.parametrize(
    "due",
    ["next tuesday", "30/04/2027", "2027-13-45", "2027-02-30", "2027-4-30", "20270430"],
)
def test_malformed_due_date_is_rejected(make_rec, due):
    assert validate(make_rec(due_date=due)) == (
        False,
        [f"due_date {due!r} is not a YYYY-MM-DD date"],
    )


def test_malformed_due_date_is_rejected_even_when_not_required(make_rec):
    assert validate(make_rec(severity="P2", due_date="soon")) == (
        False,
        ["due_date 'soon' is not a YYYY-MM-DD date"],
    )


@pytest.mark.parametrize(
    "due", ["2028-02-29", " 2027-04-30 "], ids=["leap-day", "padded"]
)
def test_valid_due_dates(make_rec, due):
    assert validate(make_rec(due_date=due)) == (True, [])


@pytest.mark.parametrize(
    ("step", "flagged"),
    [
        ("Enable .github/workflows/dry_run_gate.yml", False),
        ("Rerun rerun_tests after the fix", False),
        ("Delete stale run_ directories", False),
        ("Compare with run_1782796553291", True),
        ("(run_42) retry", True),
        ("see logs:run_42", True),
    ],
    ids=[
        "dry_run_gate",
        "rerun_tests",
        "run_-no-digits",
        "run-id",
        "run-id-in-parens",
        "run-id-after-colon",
    ],
)
def test_run_id_detection_is_not_a_substring_match(make_rec, step, flagged):
    expected = ["step 1 contains run_id (move to Ref: footer)"] if flagged else []
    assert validate(make_rec(steps=[step])) == (not flagged, expected)


@pytest.mark.parametrize(
    ("headline", "flagged"),
    [
        ("run_books migration for the ingest API", False),
        ("run_1782796553291", True),
        ("run_1782796553291: DRC retry", True),
    ],
    ids=["run_-word", "bare-run-id", "run-id-prefix"],
)
def test_headline_run_id_rule(make_rec, headline, flagged):
    assert validate(make_rec(headline=headline)) == (
        not flagged,
        [H] if flagged else [],
    )
