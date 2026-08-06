"""No-op verification tests for the global incident freeze (Phase 0 Workstream B).

Run: PYTHONPATH=. /usr/bin/python3 -m pytest tests/unit/test_incident_freeze.py -q --no-cov
"""


import pytest


@pytest.fixture
def freeze_ctl(tmp_path, monkeypatch):
    # Point the module at a temp state file and reload a fresh singleton
    import core.incident_freeze as mod

    mod.DEFAULT_STATE_PATH = tmp_path / "freeze.json"
    # rebuild singleton against tmp path
    ctl = mod.FreezeControl(state_path=tmp_path / "freeze.json")
    monkeypatch.setattr(mod, "freeze", ctl)
    return ctl


def test_defaults_not_frozen(freeze_ctl):
    assert freeze_ctl.is_frozen() is False
    assert freeze_ctl.is_write_allowed("merge") is True


def test_freeze_blocks_writes(freeze_ctl):
    freeze_ctl.freeze(by="hermes", reason="drill", scope="n8n")
    assert freeze_ctl.is_frozen("n8n") is True
    assert freeze_ctl.is_write_allowed("merge", scope="n8n") is False
    # read-only scope unaffected by a scoped freeze
    assert freeze_ctl.is_write_allowed("merge", scope="github-actions") is True


def test_global_freeze_blocks_all_scopes(freeze_ctl):
    freeze_ctl.freeze(by="hermes", reason="incident", scope="global")
    assert freeze_ctl.is_frozen("agent-core") is True
    assert freeze_ctl.is_write_allowed("merge", scope="agent-core") is False
    assert freeze_ctl.is_write_allowed("merge", scope="n8n") is False


def test_idempotent_refreeze(freeze_ctl):
    r1 = freeze_ctl.freeze(by="hermes", reason="first", scope="global")
    first_at = r1["enabled_at"]
    r2 = freeze_ctl.freeze(by="hermes", reason="dup", scope="global")
    # enabled_at preserved (first cause retained), not overwritten
    assert r2["enabled_at"] == first_at
    assert r2["frozen"] is True


def test_idempotent_unfreeze_when_not_frozen(freeze_ctl):
    # disabling while not frozen must not raise
    r = freeze_ctl.unfreeze(by="hermes")
    assert r["frozen"] is False


def test_unfreeze_restores_writes(freeze_ctl):
    freeze_ctl.freeze(by="hermes", reason="x", scope="global")
    assert freeze_ctl.is_write_allowed("merge") is False
    freeze_ctl.unfreeze(by="hermes", reason="cleared")
    assert freeze_ctl.is_write_allowed("merge") is True


def test_expiry_auto_clears(freeze_ctl):
    past = "2000-01-01T00:00:00+00:00"
    freeze_ctl.freeze(by="hermes", reason="temp", scope="global", expires_at=past)
    assert freeze_ctl.is_frozen() is False  # expired on read


def test_audit_records_events(freeze_ctl):
    freeze_ctl.freeze(by="op1", reason="incident", scope="global")
    freeze_ctl.unfreeze(by="op2", reason="resolved")
    events = [a["event"] for a in freeze_ctl.status()["audit"]]
    assert "freeze-enabled" in events
    assert "freeze-disabled" in events


def test_state_persists(tmp_path):
    import core.incident_freeze as mod

    p = tmp_path / "freeze.json"
    c1 = mod.FreezeControl(state_path=p)
    c1.freeze(by="hermes", reason="persist", scope="global")
    # new instance reads the persisted file
    c2 = mod.FreezeControl(state_path=p)
    assert c2.is_frozen() is True
