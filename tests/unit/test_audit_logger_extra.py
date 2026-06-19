"""Additional unit tests for core/audit_logger.py

Supplements tests/unit/test_audit_chain.py with coverage of:
- get_logs / get_audit_trail filtering
- rollback instruction generation
- archive_logs (no-op without S3)
- get_logs from nonexistent file
- AuditLogger.close
"""

from __future__ import annotations

import asyncio
from pathlib import Path


def run(coro):
    return asyncio.run(coro)


def _make_logger(tmp_path: Path):
    from core.audit_logger import AuditLogger

    return AuditLogger({"audit_log_path": str(tmp_path / "audit.jsonl")})


class TestGetLogs:
    def test_get_logs_returns_empty_list_when_no_file(self, tmp_path):
        al = _make_logger(tmp_path)
        # Remove the file that __init__ may have created
        al.log_file.unlink(missing_ok=True)
        assert al.get_logs() == []

    def test_get_logs_returns_all_entries(self, tmp_path):
        al = _make_logger(tmp_path)
        run(al.log_action("agent_a", "create_issue", {}, {}, "t1"))
        run(al.log_action("agent_b", "merge_pr", {}, {}, "t2"))
        logs = al.get_logs()
        assert len(logs) == 2

    def test_get_logs_filters_by_agent(self, tmp_path):
        al = _make_logger(tmp_path)
        run(al.log_action("alpha", "create_issue", {}, {}, "t1"))
        run(al.log_action("beta", "create_issue", {}, {}, "t2"))
        logs = al.get_logs(agent="alpha")
        assert len(logs) == 1
        assert logs[0]["agent"] == "alpha"

    def test_get_logs_filters_by_action(self, tmp_path):
        al = _make_logger(tmp_path)
        run(al.log_action("a", "create_issue", {}, {}, "t1"))
        run(al.log_action("a", "merge_pr", {}, {}, "t2"))
        logs = al.get_logs(action="merge_pr")
        assert len(logs) == 1
        assert logs[0]["action"] == "merge_pr"

    def test_get_logs_respects_limit(self, tmp_path):
        al = _make_logger(tmp_path)
        for i in range(10):
            run(al.log_action("a", "op", {}, {}, f"t{i}"))
        logs = al.get_logs(limit=3)
        assert len(logs) == 3

    def test_get_logs_both_filters(self, tmp_path):
        al = _make_logger(tmp_path)
        run(al.log_action("alice", "create_issue", {}, {}, "t1"))
        run(al.log_action("alice", "delete_branch", {}, {}, "t2"))
        run(al.log_action("bob", "create_issue", {}, {}, "t3"))
        logs = al.get_logs(agent="alice", action="delete_branch")
        assert len(logs) == 1


class TestGetAuditTrail:
    def test_get_audit_trail_is_async_alias(self, tmp_path):
        al = _make_logger(tmp_path)
        run(al.log_action("a", "op", {}, {}, "t1"))
        trail = run(al.get_audit_trail(agent="a"))
        assert len(trail) == 1

    def test_get_audit_trail_returns_list(self, tmp_path):
        al = _make_logger(tmp_path)
        result = run(al.get_audit_trail())
        assert isinstance(result, list)


class TestRollbackInstructions:
    def _rollback(self, action, params=None, result=None):
        from core.audit_logger import AuditLogger

        al = AuditLogger.__new__(AuditLogger)
        return al._generate_rollback_instructions(action, params or {}, result or {})

    def test_create_issue_rollback(self):
        instr = self._rollback("create_issue")
        assert "Close" in instr

    def test_create_branch_rollback_includes_branch_name(self):
        instr = self._rollback("create_branch", params={"branch_name": "feat/x"})
        assert "feat/x" in instr

    def test_merge_pr_rollback(self):
        instr = self._rollback("merge_pr")
        assert "Revert" in instr

    def test_delete_branch_rollback_includes_commit(self):
        instr = self._rollback("delete_branch", result={"last_commit": "abc123"})
        assert "abc123" in instr

    def test_update_file_rollback_includes_file_path(self):
        instr = self._rollback("update_file", params={"file_path": "src/main.py"})
        assert "src/main.py" in instr

    def test_add_label_rollback_includes_label(self):
        instr = self._rollback("add_label", params={"label": "bug"})
        assert "bug" in instr

    def test_assign_issue_rollback_includes_assignee(self):
        instr = self._rollback("assign_issue", params={"assignee": "alice"})
        assert "alice" in instr

    def test_unknown_action_returns_manual_rollback(self):
        instr = self._rollback("some_unknown_action")
        assert "Manual" in instr or "N/A" in instr


class TestArchiveLogs:
    def test_archive_logs_no_op_without_s3(self, tmp_path):
        al = _make_logger(tmp_path)
        # Should log a warning but not raise
        run(al.archive_logs(older_than_days=30))


class TestClose:
    def test_close_without_pg_conn(self, tmp_path):
        al = _make_logger(tmp_path)
        al.close()  # should not raise

    def test_close_calls_pg_close(self, tmp_path):
        al = _make_logger(tmp_path)
        mock_conn = al._pg_conn = __import__(
            "unittest.mock", fromlist=["MagicMock"]
        ).MagicMock()
        al.close()
        mock_conn.close.assert_called_once()


class TestComputeChainHash:
    def test_hash_is_deterministic(self):
        from core.audit_logger import AuditLogger

        entry = {"action": "test", "params": {}}
        h1 = AuditLogger._compute_chain_hash("prev", entry)
        h2 = AuditLogger._compute_chain_hash("prev", entry)
        assert h1 == h2

    def test_different_prev_hash_produces_different_result(self):
        from core.audit_logger import AuditLogger

        entry = {"action": "test"}
        h1 = AuditLogger._compute_chain_hash("aaa", entry)
        h2 = AuditLogger._compute_chain_hash("bbb", entry)
        assert h1 != h2

    def test_hash_is_64_hex_chars(self):
        from core.audit_logger import AuditLogger

        h = AuditLogger._compute_chain_hash("0" * 64, {"action": "x"})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
