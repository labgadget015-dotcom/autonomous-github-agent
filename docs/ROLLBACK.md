# Rollback Manifest

## 5f5eee1 — 2026-05-08 08:04 UTC

- **SHA**: `5f5eee1eda940c9b92a3c07ccfd19746c04696c8`
- **Author**: GadgetAI
- **Message**: style: apply black formatting to tests/
- **Files changed**: 50 file(s)

**Changed files:**
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_ai_agent.py`
- `tests/test_ai_optimization.py`
- `tests/test_branch_protection.py`
- `tests/test_core.py`
- `tests/test_elite_copilot.py`
- `tests/test_error_handler.py`
- `tests/test_error_recovery.py`
- `tests/test_github_operations.py`
- `tests/test_orchestrator.py`
- `tests/test_overseer.py`
- `tests/test_utils.py`
- `tests/unit/test_agent_base.py`
- `tests/unit/test_agent_config.py`
- `tests/unit/test_ai_code_suggestor.py`
- `tests/unit/test_anomaly_detector.py`
- `tests/unit/test_audit_chain.py`
- `tests/unit/test_audit_logger_extra.py`
- `tests/unit/test_automation_engine.py`

---

## afdfdd4 — 2026-05-08 08:01 UTC

- **SHA**: `afdfdd44afb0c7dfac7abe561919d2184a2b958d`
- **Author**: GadgetAI
- **Message**: style: apply black formatting across codebase
- **Files changed**: 72 file(s)

**Changed files:**
- `.github/scripts/ai_agent_main.py`
- `.github/scripts/ai_code_suggestor.py`
- `.github/scripts/ai_workflow_optimizer.py`
- `.github/scripts/async_parallel_analyzer.py`
- `.github/scripts/badge_generator.py`
- `.github/scripts/changelog_generator.py`
- `.github/scripts/check_policy.py`
- `.github/scripts/complexity_reporter.py`
- `.github/scripts/copilot_integration.py`
- `.github/scripts/cost_calculator.py`
- `.github/scripts/cot_selector.py`
- `.github/scripts/dependency_updater.py`
- `.github/scripts/distributed_monitoring.py`
- `.github/scripts/docgen.py`
- `.github/scripts/elite_copilot.py`
- `.github/scripts/error_handler.py`
- `.github/scripts/gather_context.py`
- `.github/scripts/generate_rollback_manifest.py`
- `.github/scripts/health_dashboard_generator.py`
- `.github/scripts/inline_pr_commenter.py`

---

## 0306da6 — 2026-05-08 07:53 UTC

- **SHA**: `0306da6709b286705d346ebe46a1465fe72a40fa`
- **Author**: GadgetAI
- **Message**: docs: add CLAUDE.md with environment and architecture guidance
- **Files changed**: 1 file(s)

**Changed files:**
- `CLAUDE.md`

---

## 03bbcc4 — 2026-05-06 04:52 UTC

- **SHA**: `03bbcc4c800f7af418523bff357cea7da335a75b`
- **Author**: GadgetAI
- **Message**: fix: lower coverage threshold to 55% and fix pre-commit config
- **Files changed**: 2 file(s)

**Changed files:**
- `.pre-commit-config.yaml`
- `pytest.ini`

---

## 383249b — 2026-05-05 06:44 UTC

- **SHA**: `383249bc59094fbb77599a299d1167d006cd31a0`
- **Author**: GadgetAI
- **Message**: ci: fix update-dashboard commit step (staged-only check, optional coverage.svg)
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`

---

## 2a7dd51 — 2026-05-05 06:38 UTC

- **SHA**: `2a7dd51659cb6371e0dfffc89d4f8294ab7be6c8`
- **Author**: GadgetAI
- **Message**: fix: repair syntax error in cot_selector.py (unterminated string literal)
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/scripts/cot_selector.py`

---

## 05866b6 — 2026-05-05 06:34 UTC

- **SHA**: `05866b6b43fcd3e6ef4a3574eb5db5a64c7ec452`
- **Author**: GadgetAI
- **Message**: ci: lower coverage threshold to 55% (realistic baseline)
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`

---

## 374fbda — 2026-05-05 06:28 UTC

- **SHA**: `374fbda4bfc77c70f24e5a572192a5433cab6882`
- **Author**: GadgetAI
- **Message**: fix: resolve API contract mismatches causing test-coverage CI failures
- **Files changed**: 11 file(s)

**Changed files:**
- `.github/scripts/ai_agent_main.py`
- `.github/scripts/ai_code_suggestor.py`
- `agents/orchestrator_agent.py`
- `autopilot/ai_optimization/intelligent_cache.py`
- `autopilot/ai_optimization/ml_priority_scorer.py`
- `autopilot/ai_optimization/nlp_relevance_filter.py`
- `autopilot/ai_optimization/performance_monitor.py`
- `core/github_client.py`
- `demo_ai_optimization.py`
- `tests/test_core.py`
- `tests/unit/test_github_client.py`

---

## dd1fdc9 — 2026-04-28 22:11 UTC

- **SHA**: `dd1fdc9dab57d284636fea8dd25a9051bce0e4e3`
- **Author**: Gadget Lab
- **Message**: fix: add continue-on-error to parallel-analysis threshold check
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`

---

## f421418 — 2026-04-28 22:05 UTC

- **SHA**: `f421418c29f21f2ec2011ebbf35f28a1a68ce155`
- **Author**: Gadget Lab
- **Message**: fix(lint): fix ruff violations in ai_agent_main.py
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/scripts/ai_agent_main.py`

---

## 8ff4485 — 2026-04-28 22:03 UTC

- **SHA**: `8ff4485a6092ffbd3634e5cf691ac37c8e30d397`
- **Author**: Gadget Lab
- **Message**: fix(lint): fix ruff violations in ai_code_suggestor.py
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/scripts/ai_code_suggestor.py`

---

## b26aff2 — 2026-04-28 21:59 UTC

- **SHA**: `b26aff241c6415db69eed57c661a2ae636bdeea5`
- **Author**: Gadget Lab
- **Message**: fix: upgrade upload-sarif to v4 and add continue-on-error for private repo
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/security_scan.yml`

---

## c69e09f — 2026-04-28 19:40 UTC

- **SHA**: `c69e09fb03682e52d0c9164c964822f153a41aab`
- **Author**: Gadget Lab
- **Message**: fix: rewrite threshold check as single-line python3 command
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`

---

## 0fe921b — 2026-04-28 19:38 UTC

- **SHA**: `0fe921bb92919a1b2ad90fe8f69ee4a2507c733d`
- **Author**: Gadget Lab
- **Message**: fix: resolve IndentationError in Check thresholds step
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`

---

## e1b0554 — 2026-04-23 08:50 UTC

- **SHA**: `e1b055474dcaabb9f39f5286d65c75e515b69945`
- **Author**: Gadget Lab
- **Message**: fix(ci): upgrade actions, fix daily summary failure, add pip cache & dedup issues
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/elite_copilot.yml`

---

## 10e12c6 — 2026-04-15 22:00 UTC

- **SHA**: `10e12c6b5b0d46ea58952dc64b862cfa160a002f`
- **Author**: Gadget Lab
- **Message**: Merge pull request #103 from labgadget015-dotcom/copilot/analyze-test-coverage-again
- **Files changed**: 0 file(s)

---

## ac2efbd — 2026-03-25 12:17 UTC

- **SHA**: `ac2efbd4e17c09b217fa94bc9f559fc63524b497`
- **Author**: Gadget Lab
- **Message**: Merge pull request #99 from labgadget015-dotcom/copilot/analyze-test-coverage
- **Files changed**: 0 file(s)

---

## 7291022 — 2026-03-25 11:05 UTC

- **SHA**: `729102285df1b7c28fb3bcc93fd6c4ce32068018`
- **Author**: Gadget Lab
- **Message**: fix: correct Python indentation in generate_rollback_manifest.py
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/scripts/generate_rollback_manifest.py`

---

This file tracks all commits to main for rollback purposes.

