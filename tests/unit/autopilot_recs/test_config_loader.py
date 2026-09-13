"""Tests for autopilot/config_loader.py.

File access is mocked (``os.path.exists`` + a module-scoped ``open``) wherever
the test is about *whether and how* the file is read; real temp files are used
only where YAML parsing of a whole document is the point.
"""

from __future__ import annotations

import copy
import sys
from unittest import mock

import pytest
import yaml

from tests.unit.autopilot_recs._support import REAL_CONFIG

# isort: split
import config_loader  # noqa: E402
from config_loader import DEFAULTS  # noqa: E402
from recommendation_contract import VALID_STATUSES  # noqa: E402

VIRTUAL = "/virtual/config.yaml"


def _mock_file(text: str | None):
    """Patch exists() and a module-local open() so no real file is touched.

    ``text=None`` means the file does not exist.
    """
    exists = mock.patch.object(
        config_loader.os.path, "exists", return_value=text is not None
    )
    opener = mock.patch(
        "config_loader.open", mock.mock_open(read_data=text or ""), create=True
    )
    return exists, opener


# --------------------------------------------------------------------------- #
# load_config: file presence, parsing, fallbacks
# --------------------------------------------------------------------------- #


def test_missing_file_returns_defaults_without_opening():
    exists_patch, open_patch = _mock_file(None)
    with exists_patch as exists, open_patch as m_open:
        cfg = config_loader.load_config(VIRTUAL)
    assert cfg == DEFAULTS
    exists.assert_called_once_with(VIRTUAL)
    m_open.assert_not_called()


def test_result_is_a_deep_copy_of_defaults():
    cfg = config_loader.load_config()
    snapshot = copy.deepcopy(DEFAULTS)
    cfg["status_tags"]["open"] = "mutated"
    cfg["recommendation_debounce"]["repost_policy"]["open"]["min_hours_between"] = 1
    assert DEFAULTS == snapshot


def test_file_is_opened_as_utf8():
    exists_patch, open_patch = _mock_file("status_tags:\n  open: 'X'\n")
    with exists_patch, open_patch as m_open:
        cfg = config_loader.load_config(VIRTUAL)
    m_open.assert_called_once_with(VIRTUAL, encoding="utf-8")
    assert cfg["status_tags"]["open"] == "X"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "# comment only\n",
        "null\n",
        "~\n",
        "[]\n",
        "- a\n- b\n",
        "42\n",
        "false\n",
        "plain string\n",
    ],
    ids=[
        "empty",
        "comment",
        "null",
        "tilde",
        "empty-list",
        "list",
        "int",
        "false",
        "scalar-str",
    ],
)
def test_non_mapping_yaml_falls_back_to_defaults(text):
    exists_patch, open_patch = _mock_file(text)
    with exists_patch, open_patch:
        assert config_loader.load_config(VIRTUAL) == DEFAULTS


@pytest.mark.parametrize(
    "text",
    ["key: [unclosed", "a: b: c", "\tfoo: bar", "{", "x: 'unterminated"],
    ids=["unclosed-flow", "nested-colon", "tab-indent", "lone-brace", "open-quote"],
)
def test_malformed_yaml_raises_and_does_not_poison_cache(text):
    # Not caught by the loader: a corrupt config.yaml crashes every caller.
    exists_patch, open_patch = _mock_file(text)
    with exists_patch, open_patch, pytest.raises(yaml.YAMLError):
        config_loader.load_config(VIRTUAL)
    assert config_loader._cache is None
    # Once the file is gone, the next call recovers cleanly.
    exists_patch, open_patch = _mock_file(None)
    with exists_patch, open_patch:
        assert config_loader.load_config(VIRTUAL) == DEFAULTS


def test_without_pyyaml_the_file_is_never_consulted(monkeypatch):
    monkeypatch.setitem(sys.modules, "yaml", None)  # makes `import yaml` fail
    with (
        mock.patch.object(config_loader.os.path, "exists") as exists,
        mock.patch("config_loader.open", create=True) as m_open,
    ):
        assert config_loader.load_config(VIRTUAL) == DEFAULTS
    exists.assert_not_called()
    m_open.assert_not_called()


# --------------------------------------------------------------------------- #
# caching
# --------------------------------------------------------------------------- #


def test_path_none_reads_default_path_at_call_time(monkeypatch):
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", "/virtual/late.yaml")
    exists_patch, open_patch = _mock_file(None)
    with exists_patch as exists, open_patch:
        config_loader.load_config()
    exists.assert_called_once_with("/virtual/late.yaml")


def test_cached_result_ignores_a_different_path(write_config, tmp_path):
    write_config("message_contract:\n  max_step_len: 10\n")
    first = config_loader.load_config()
    other = tmp_path / "other.yaml"
    other.write_text("message_contract:\n  max_step_len: 99\n", encoding="utf-8")
    with mock.patch.object(config_loader.os.path, "exists") as exists:
        second = config_loader.load_config(str(other))
    assert second is first
    assert second["message_contract"]["max_step_len"] == 10
    exists.assert_not_called()


def test_reset_cache_forces_a_reread(write_config):
    write_config("message_contract:\n  max_step_len: 10\n")
    assert config_loader.get_contract()["max_step_len"] == 10
    write_config("message_contract:\n  max_step_len: 55\n")  # also resets
    assert config_loader.get_contract()["max_step_len"] == 55


# --------------------------------------------------------------------------- #
# _deep_merge
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("base", "over", "expected"),
    [
        ({"a": {"x": 1, "y": 2}}, {"a": {"y": 3}}, {"a": {"x": 1, "y": 3}}),
        (
            {"a": {"b": {"c": 1, "d": 2}}},
            {"a": {"b": {"d": 9}}},
            {"a": {"b": {"c": 1, "d": 9}}},
        ),
        ({"a": {"x": 1}}, {"a": 5}, {"a": 5}),
        ({"a": 5}, {"a": {"x": 1}}, {"a": {"x": 1}}),
        ({"a": {"x": 1}}, {"a": None}, {"a": None}),
        ({"a": [1, 2]}, {"a": [3]}, {"a": [3]}),
        ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
        ({"a": {"x": 1}}, {}, {"a": {"x": 1}}),
        ({}, {"a": {"x": 1}}, {"a": {"x": 1}}),
    ],
    ids=[
        "nested-partial",
        "three-levels",
        "scalar-replaces-dict",
        "dict-replaces-scalar",
        "none-replaces-dict",
        "lists-replaced-not-merged",
        "new-key-added",
        "empty-override",
        "empty-base",
    ],
)
def test_deep_merge(base, over, expected):
    result = config_loader._deep_merge(base, over)
    assert result == expected
    assert result is base  # merges in place


# --------------------------------------------------------------------------- #
# getters
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("open", 72),
        ("assigned", 168),
        ("inflight", 168),
        ("done", None),
        ("dropped", None),
        ("unknown", 72),
        ("", 72),
        ("OPEN", 72),  # lookup is case-sensitive; falls to the 72h default
    ],
)
def test_debounce_hours_defaults(status, expected):
    assert config_loader.get_debounce_hours(status) == expected


@pytest.mark.parametrize(
    ("policy_yaml", "status", "expected"),
    [
        ("open: {never_repost: true}", "open", None),
        ("open: {never_repost: 'yes'}", "open", None),
        ("open: {min_hours_between: 0}", "open", 0),
        ("open: {min_hours_between: 1000000}", "open", 1000000),
        ("done: {never_repost: false}", "done", 72),
        # Keys the code does not read are ignored — mirrors the live config.yaml,
        # which sets require_status_change / require_owner_change.
        ("open: {min_hours_between: 72, require_status_change: true}", "open", 72),
        ("custom: {min_hours_between: 5}", "custom", 5),
    ],
    ids=[
        "never-repost-true",
        "never-repost-truthy-str",
        "zero-window-not-none",
        "huge-window",
        "unban-done-gets-default",
        "unread-keys-ignored",
        "custom-status",
    ],
)
def test_debounce_hours_overrides(write_config, policy_yaml, status, expected):
    write_config(f"recommendation_debounce:\n  repost_policy:\n    {policy_yaml}\n")
    assert config_loader.get_debounce_hours(status) == expected


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("open", "🟡 Open"),
        ("assigned", "🔵 Assigned"),
        ("inflight", "🟠 In-flight"),
        ("done", "✅ Done"),
        ("dropped", "❌ Dropped"),
        ("unknown", "🟡 Open"),
        ("", "🟡 Open"),
        ("Done", "🟡 Open"),
    ],
)
def test_status_tag_defaults(status, expected):
    assert config_loader.get_status_tag(status) == expected


def test_status_tag_override(write_config):
    write_config("status_tags:\n  done: 'SHIPPED'\n")
    assert config_loader.get_status_tag("done") == "SHIPPED"
    assert config_loader.get_status_tag("open") == "🟡 Open"


def test_get_contract_is_the_live_section():
    contract = config_loader.get_contract()
    assert contract == DEFAULTS["message_contract"]
    assert contract is config_loader.load_config()["message_contract"]


def test_ledger_path_default_and_override(write_config):
    assert (
        config_loader.get_ledger_path() == "autopilot/decisions/recommendations.jsonl"
    )
    write_config("recommendation_debounce:\n  ledger_path: /data/recs.jsonl\n")
    assert config_loader.get_ledger_path() == "/data/recs.jsonl"


def test_ledger_path_falls_back_when_key_absent(monkeypatch):
    # Unreachable through YAML (deep-merge keeps the default key), so stub the loader.
    monkeypatch.setattr(
        config_loader, "load_config", lambda: {"recommendation_debounce": {}}
    )
    assert (
        config_loader.get_ledger_path() == "autopilot/decisions/recommendations.jsonl"
    )


@pytest.mark.parametrize(
    ("text", "call", "exc"),
    [
        (
            "status_tags: null\n",
            lambda: config_loader.get_status_tag("open"),
            AttributeError,
        ),
        (
            "recommendation_debounce: []\n",
            lambda: config_loader.get_debounce_hours("open"),
            TypeError,
        ),
        (
            "recommendation_debounce:\n  repost_policy: 7\n",
            lambda: config_loader.get_debounce_hours("open"),
            AttributeError,
        ),
        (
            "recommendation_debounce:\n  repost_policy:\n    open: 3\n",
            lambda: config_loader.get_debounce_hours("open"),
            AttributeError,
        ),
    ],
    ids=["tags-null", "debounce-list", "policy-scalar", "status-policy-scalar"],
)
def test_wrong_typed_section_replaces_default_and_crashes_getter(
    write_config, text, call, exc
):
    # The loader does no shape validation: a wrong-typed section overwrites the
    # default wholesale and the error surfaces later, in the getter.
    write_config(text)
    with pytest.raises(exc):
        call()


# --------------------------------------------------------------------------- #
# drift guard: the committed config.yaml vs the built-in defaults
# --------------------------------------------------------------------------- #


def test_repo_config_agrees_with_defaults_for_every_key_the_code_reads(monkeypatch):
    # 1) Load the committed config.yaml and read every value through the getters.
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", str(REAL_CONFIG))
    config_loader.reset_cache()
    cfg = config_loader.load_config()
    live = {
        "status_tags": cfg["status_tags"],
        "message_contract": cfg["message_contract"],
        "ledger_path": config_loader.get_ledger_path(),
        "debounce": {s: config_loader.get_debounce_hours(s) for s in VALID_STATUSES},
    }

    # 2) Same reads against the built-in DEFAULTS only.
    monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", "/virtual/absent.yaml")
    config_loader.reset_cache()
    builtin = {
        "status_tags": DEFAULTS["status_tags"],
        "message_contract": DEFAULTS["message_contract"],
        "ledger_path": config_loader.get_ledger_path(),
        "debounce": {s: config_loader.get_debounce_hours(s) for s in VALID_STATUSES},
    }
    assert live == builtin
