"""Unit tests for core/policy_engine.py"""

from __future__ import annotations

import asyncio
import pytest

from core.policy_engine import PolicyEngine


def run(coro):
    return asyncio.run(coro)


class TestPolicyEngineInit:
    def test_default_policies_loaded_when_file_missing(self):
        engine = PolicyEngine({"policy_file": "/nonexistent/path.yaml"})
        policies = engine.get_policies()
        assert "requires_approval" in policies
        assert "auto_approved" in policies

    def test_config_overrides_policy_lists(self):
        engine = PolicyEngine(
            {
                "policy_file": "/nonexistent/path.yaml",
                "auto_approved": ["my_action"],
                "requires_approval": ["danger_action"],
            }
        )
        policies = engine.get_policies()
        assert "my_action" in policies["auto_approved"]
        assert "danger_action" in policies["requires_approval"]

    def test_policy_file_loaded_from_disk(self, sample_policy_file):
        engine = PolicyEngine({"policy_file": sample_policy_file})
        policies = engine.get_policies()
        assert "delete_repository" in policies["requires_approval"]
        assert "label_issue" in policies["auto_approved"]


class TestCheckAction:
    def _engine(self):
        return PolicyEngine({"policy_file": "/nonexistent/path.yaml"})

    def test_auto_approved_action_is_allowed(self):
        engine = self._engine()
        result = run(engine.check_action("label_issue", {}))
        assert result["requires_approval"] is False

    def test_requires_approval_action_blocked(self):
        engine = self._engine()
        result = run(engine.check_action("delete_repository", {}))
        assert result["requires_approval"] is True
        assert "reason" in result

    def test_default_action_is_approved(self):
        engine = self._engine()
        result = run(engine.check_action("some_unknown_action", {}))
        assert result["requires_approval"] is False

    def test_destructive_action_name_blocked(self):
        engine = self._engine()
        result = run(engine.check_action("delete_temp_files", {}))
        assert result["requires_approval"] is True

    def test_remove_keyword_detected_as_destructive(self):
        engine = self._engine()
        result = run(engine.check_action("remove_old_records", {}))
        assert result["requires_approval"] is True

    def test_force_keyword_detected_as_destructive(self):
        engine = self._engine()
        result = run(engine.check_action("force_update", {}))
        assert result["requires_approval"] is True

    def test_protected_branch_merge_requires_approval(self):
        engine = self._engine()
        result = run(engine.check_action("merge", {"branch": "main"}))
        assert result["requires_approval"] is True

    def test_protected_branch_production_requires_approval(self):
        engine = self._engine()
        result = run(engine.check_action("merge", {"branch": "production"}))
        assert result["requires_approval"] is True

    def test_non_protected_branch_merge_allowed(self):
        engine = self._engine()
        result = run(engine.check_action("merge", {"branch": "feature/my-branch"}))
        # 'merge' is not in the default requires_approval list and not destructive by name
        # branch is not main/master/production, so should be allowed
        assert result["requires_approval"] is False

    def test_result_contains_escalation_users(self):
        engine = self._engine()
        result = run(engine.check_action("delete_repository", {}))
        assert "escalation_users" in result


class TestApprovalRuleManagement:
    def _engine(self):
        return PolicyEngine({"policy_file": "/nonexistent/path.yaml"})

    def test_add_approval_rule(self):
        engine = self._engine()
        engine.add_approval_rule("new_dangerous_action")
        result = run(engine.check_action("new_dangerous_action", {}))
        assert result["requires_approval"] is True

    def test_add_approval_rule_not_duplicated(self):
        engine = self._engine()
        engine.add_approval_rule("delete_repository")
        policy_list = engine.get_policies()["requires_approval"]
        assert policy_list.count("delete_repository") == 1

    def test_remove_approval_rule(self):
        engine = self._engine()
        engine.remove_approval_rule("delete_repository")
        policies = engine.get_policies()
        assert "delete_repository" not in policies["requires_approval"]

    def test_remove_nonexistent_rule_is_noop(self):
        engine = self._engine()
        engine.remove_approval_rule("nonexistent_action")  # should not raise

    def test_get_policies_returns_copy(self):
        engine = self._engine()
        policies_a = engine.get_policies()
        policies_b = engine.get_policies()
        assert policies_a is not policies_b


class TestSavePolicies:
    def test_save_and_reload_policies(self, tmp_path):
        policy_file = str(tmp_path / "policies.yaml")
        engine = PolicyEngine({"policy_file": "/nonexistent/path.yaml"})
        engine.add_approval_rule("custom_action")
        engine.save_policies(policy_file)

        engine2 = PolicyEngine({"policy_file": policy_file})
        assert "custom_action" in engine2.get_policies()["requires_approval"]

    def test_save_uses_default_policy_file_from_config(self, tmp_path):
        policy_file = str(tmp_path / "sub" / "policies.yaml")
        engine = PolicyEngine({"policy_file": policy_file})
        # Should create parent directory and save
        engine.save_policies()
        import yaml
        from pathlib import Path
        with open(policy_file) as f:
            data = yaml.safe_load(f)
        assert "requires_approval" in data


class TestIsDestructiveAction:
    def _engine(self):
        return PolicyEngine({})

    def test_destroy_keyword(self):
        engine = self._engine()
        assert engine._is_destructive_action("destroy_database", {}) is True

    def test_drop_keyword(self):
        engine = self._engine()
        assert engine._is_destructive_action("drop_table", {}) is True

    def test_non_destructive_action(self):
        engine = self._engine()
        assert engine._is_destructive_action("create_branch", {}) is False

    def test_master_branch_delete_is_destructive(self):
        engine = self._engine()
        assert engine._is_destructive_action("delete", {"branch": "master"}) is True
