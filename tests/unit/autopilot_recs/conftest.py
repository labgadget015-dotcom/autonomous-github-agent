"""Fixtures for the autopilot recommendation-pipeline tests.

Determinism comes from global state, not the filesystem: ``config_loader``
caches its config module-wide, and importing ``decisions.ledger`` populates that
cache from the CWD-relative ``autopilot/config.yaml``. Every test therefore
starts from the built-in DEFAULTS with a cold cache.
"""

from __future__ import annotations

import pytest

from tests.unit.autopilot_recs._support import GOOD_FIELDS, REAL_LEDGER

# isort: split
import config_loader  # noqa: E402  (importable only after _support runs)
from recommendation_contract import Recommendation  # noqa: E402


def _real_ledger_fingerprint() -> int | None:
    return REAL_LEDGER.stat().st_mtime_ns if REAL_LEDGER.exists() else None


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point the loader at a file that does not exist and clear the cache on
    both sides. Also fail loudly if a test touched the real ledger: the ledger
    functions bind their default ``path`` at import time, so a forgotten
    ``path=`` argument writes into the repo."""
    monkeypatch.setattr(
        config_loader, "DEFAULT_CONFIG_PATH", str(tmp_path / "no-such-config.yaml")
    )
    config_loader.reset_cache()
    before = _real_ledger_fingerprint()
    yield
    config_loader.reset_cache()
    assert (
        _real_ledger_fingerprint() == before
    ), f"a test wrote to the real ledger {REAL_LEDGER}; pass path= explicitly"


@pytest.fixture
def write_config(tmp_path, monkeypatch):
    """Write YAML to a temp config file and make it the active config."""

    def _write(text: str):
        path = tmp_path / "config.yaml"
        path.write_text(text, encoding="utf-8")
        monkeypatch.setattr(config_loader, "DEFAULT_CONFIG_PATH", str(path))
        config_loader.reset_cache()
        return path

    return _write


@pytest.fixture
def make_rec():
    """Build a valid P0 Recommendation, overriding any fields given."""

    def _make(**overrides) -> Recommendation:
        fields = {**GOOD_FIELDS, "steps": list(GOOD_FIELDS["steps"])}
        fields.update(overrides)
        return Recommendation(**fields)

    return _make
