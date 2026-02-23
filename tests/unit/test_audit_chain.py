"""Unit tests for hash-chained audit log (core/audit_logger.py)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path


def run(coro):
    return asyncio.run(coro)


class TestHashChain:
    def _make_logger(self, tmp_path: Path):
        from core.audit_logger import AuditLogger
        cfg = {"audit_log_path": str(tmp_path / "audit.jsonl")}
        return AuditLogger(cfg)

    def test_single_entry_has_chain_hash(self, tmp_path):
        al = self._make_logger(tmp_path)
        run(al.log_action("agent_x", "create_issue", {}, {"number": 1}, "t1"))
        lines = (tmp_path / "audit.jsonl").read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert "chain_hash" in entry
        assert len(entry["chain_hash"]) == 64

    def test_chain_verifies_intact(self, tmp_path):
        al = self._make_logger(tmp_path)
        run(al.log_action("a", "op1", {}, {}, "t1"))
        run(al.log_action("a", "op2", {}, {}, "t2"))
        run(al.log_action("a", "op3", {}, {}, "t3"))
        ok, errors = al.verify_chain()
        assert ok is True
        assert errors == []

    def test_tampered_entry_detected(self, tmp_path):
        al = self._make_logger(tmp_path)
        run(al.log_action("a", "op1", {}, {}, "t1"))
        run(al.log_action("a", "op2", {}, {}, "t2"))

        # Tamper with line 1
        log_file = tmp_path / "audit.jsonl"
        lines = log_file.read_text().strip().splitlines()
        entry = json.loads(lines[0])
        entry["action"] = "TAMPERED"
        lines[0] = json.dumps(entry)
        log_file.write_text("\n".join(lines) + "\n")

        ok, errors = al.verify_chain()
        assert ok is False
        assert len(errors) >= 1

    def test_empty_log_verifies_ok(self, tmp_path):
        al = self._make_logger(tmp_path)
        ok, errors = al.verify_chain()
        assert ok is True
        assert errors == []

    def test_chain_head_persists_across_instances(self, tmp_path):
        """New AuditLogger instance reading existing file continues chain."""
        from core.audit_logger import AuditLogger
        cfg = {"audit_log_path": str(tmp_path / "audit.jsonl")}
        al1 = AuditLogger(cfg)
        run(al1.log_action("a", "op1", {}, {}, "t1"))

        al2 = AuditLogger(cfg)
        run(al2.log_action("a", "op2", {}, {}, "t2"))

        ok, errors = al2.verify_chain()
        assert ok is True
