# Rollback Manifest

## 0cc1856 — 2026-07-22 06:39 UTC

- **SHA**: `0cc18568a39373a824b46a00b774c7515521ce1a`
- **Author**: Gadget Lab
- **Message**: fix(ci): correct malformed YAML in quality-ratchet.yml (#220)
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/quality-ratchet.yml`

---

## 6905e8f — 2026-07-19 22:16 UTC

- **SHA**: `6905e8f5779154e291b1aae78a057692aeb18123`
- **Author**: Gadget Lab
- **Message**: fix(ci): scope pre-commit auto-fix to PR-diff files only (#213)
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/pre-commit-ci.yml`

---

## 7efb5d2 — 2026-07-18 06:37 UTC

- **SHA**: `7efb5d2a35b37b6f171e3b1c3b88bef66a94d74b`
- **Author**: Gadget Lab
- **Message**: feat(watchdog): monitor autonomy kill-switch (dry_run/require_approval/auto_merge) (#209)
- **Files changed**: 1 file(s)

**Changed files:**
- `scripts/gadgetlab_maintenance_check.py`

---

## 882a6a7 — 2026-07-18 06:31 UTC

- **SHA**: `882a6a755dcee0c9175fd8e4695d04918eb1c201`
- **Author**: Gadget Lab
- **Message**: docs(vision): mark 'compress timelines' as measured via DORA lead-time metric (#208)
- **Files changed**: 1 file(s)

**Changed files:**
- `docs/SCALE_GOVERNANCE_VISION.md`

---

## f02f1d9 — 2026-07-18 06:20 UTC

- **SHA**: `f02f1d9101b4b0d22402ee266192810bca1d9afe`
- **Author**: Gadget Lab
- **Message**: feat(vision): stateful-scale governance vision + scale-guardrail watchdog (#207)
- **Files changed**: 2 file(s)

**Changed files:**
- `docs/SCALE_GOVERNANCE_VISION.md`
- `scripts/gadgetlab_maintenance_check.py`

---

## fde9788 — 2026-07-18 06:11 UTC

- **SHA**: `fde9788e4b6f11a94ae3ba4158838b9b41962575`
- **Author**: Gadget Lab
- **Message**: feat(autonomy): human-gated autonomy guardrails + local routing fix (#206)
- **Files changed**: 5 file(s)

**Changed files:**
- `.github/scripts/llm_router.py`
- `docs/STRATEGIC_VISION_HUMAN_GATED_AUTONOMY.md`
- `docs/human-in-the-loop-protocol.md`
- `tests/agent_drift_eval.py`
- `tests/fixtures/agent_drift_golden.json`

---

## ff8e4f6 — 2026-07-17 07:50 UTC

- **SHA**: `ff8e4f67797d3d37736e4ae607400b9d23fa01a2`
- **Author**: Gadget Lab
- **Message**: chore: prune dead ledger functions + apply pre-commit import hygiene (#203)
- **Files changed**: 3 file(s)

**Changed files:**
- `autopilot/config_loader.py`
- `autopilot/decisions/ledger.py`
- `autopilot/tests/test_recommendation_contract.py`

---

## 1f8b7e9 — 2026-07-12 06:26 UTC

- **SHA**: `1f8b7e90825cdc01f4a676693c2abd5f083be379`
- **Author**: Gadget Lab
- **Message**: Merge pull request #174 from labgadget015-dotcom/copilot/autonomous-github-agent-actions
- **Files changed**: 0 file(s)

---

## 46e776a — 2026-07-06 05:39 UTC

- **SHA**: `46e776a61296badbbefb0561bace1b8404bcdd73`
- **Author**: Gadget Lab
- **Message**: Merge pull request #190 from labgadget015-dotcom/docs/drc-token-and-infra-inventory
- **Files changed**: 0 file(s)

---

## ce5dbd9 — 2026-07-01 05:18 UTC

- **SHA**: `ce5dbd94c82e7eee8dd459d0f64543df1a46235d`
- **Author**: Gadget Lab
- **Message**: docs: update contact email to labgadget015@gmail.com
- **Files changed**: 1 file(s)

**Changed files:**
- `README.md`

---

## ac7d664 — 2026-07-01 05:07 UTC

- **SHA**: `ac7d6648d381ebab64cf23442e25b47c0aeaef51`
- **Author**: Gadget Lab
- **Message**: docs: add Work With Gadget Lab CTA section to README
- **Files changed**: 1 file(s)

**Changed files:**
- `README.md`

---

## a45ba72 — 2026-06-30 05:38 UTC

- **SHA**: `a45ba72e472bcc7d3b7ef8ea85bc6db85fa390b7`
- **Author**: GadgetAI
- **Message**: fix: black format 6 test files + retry push loop in all 4 commit workflows
- **Files changed**: 10 file(s)

**Changed files:**
- `.github/workflows/changelog.yml`
- `.github/workflows/pre-commit-ci.yml`
- `.github/workflows/security_scan.yml`
- `.github/workflows/test_metrics.yml`
- `tests/test_autonomous_agents.py`
- `tests/unit/test_autopilot.py`
- `tests/unit/test_code_review_agent.py`
- `tests/unit/test_dependency_agent.py`
- `tests/unit/test_security_scan_agent.py`
- `tests/unit/test_triage_agent.py`

---

## ba1a987 — 2026-06-30 05:29 UTC

- **SHA**: `ba1a9877fd85a4c416c0f0115b29c1538c6843e7`
- **Author**: GadgetAI
- **Message**: fix(workflows): git pull --rebase before push in security_scan, test_metrics, pre-commit-ci
- **Files changed**: 3 file(s)

**Changed files:**
- `.github/workflows/pre-commit-ci.yml`
- `.github/workflows/security_scan.yml`
- `.github/workflows/test_metrics.yml`

---

## f90c4de — 2026-06-30 05:25 UTC

- **SHA**: `f90c4dec919dd1b52b3b7c669106e34418eacf82`
- **Author**: GadgetAI
- **Message**: test: add 97 unit tests for autopilot, code_review, dependency, security_scan, triage agents
- **Files changed**: 5 file(s)

**Changed files:**
- `tests/unit/test_autopilot.py`
- `tests/unit/test_code_review_agent.py`
- `tests/unit/test_dependency_agent.py`
- `tests/unit/test_security_scan_agent.py`
- `tests/unit/test_triage_agent.py`

---

## f2492bc — 2026-06-30 05:24 UTC

- **SHA**: `f2492bcdabab87c2f73bf569b8c93a367514a414`
- **Author**: GadgetAI
- **Message**: fix(changelog): git pull --rebase before push to handle concurrent workflow collisions
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/changelog.yml`

---

## 9cb29a6 — 2026-06-30 05:21 UTC

- **SHA**: `9cb29a65836ffc5eb1969149dd5ed123d06221e0`
- **Author**: GadgetAI
- **Message**: fix(test): update llm_router complexity thresholds to match new routing logic
- **Files changed**: 1 file(s)

**Changed files:**
- `tests/unit/test_llm_router.py`

---

## d4257f8 — 2026-06-30 05:18 UTC

- **SHA**: `d4257f8ba65ea5b51e57dbb61371393557de1243`
- **Author**: GadgetAI
- **Message**: fix(n8n-health-check): only alert on host down, not DRC timeout
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/n8n-health-check.yml`

---

## 70bc0ca — 2026-06-30 05:14 UTC

- **SHA**: `70bc0cabc4e76a8b29deb4d9860db6433baf6faf`
- **Author**: GadgetAI
- **Message**: fix(n8n-health-check): continue-on-error + 30s timeout for DRC probe
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/n8n-health-check.yml`

---

## 7eb4212 — 2026-06-30 05:11 UTC

- **SHA**: `7eb4212fd82a83d4d4e38abc63e2162650faea17`
- **Author**: GadgetAI
- **Message**: feat: pipeline enchantments — coverage, cost cap, PAT alert, n8n health, Grafana, LLM routing
- **Files changed**: 8 file(s)

**Changed files:**
- `.github/scripts/llm_router.py`
- `.github/workflows/n8n-health-check.yml`
- `.github/workflows/pat-rotation-alert.yml`
- `core/llm_provider.py`
- `monitoring/grafana-dashboards/dashboards.yml`
- `monitoring/grafana-dashboards/repository-health.json`
- `pyproject.toml`
- `pytest.ini`

---

## c515a21 — 2026-06-29 06:20 UTC

- **SHA**: `c515a212be4dd45a73bc1bc3405ff60367e5a3a9`
- **Author**: GadgetAI
- **Message**: fix(ci): fix IndexError on empty aliases + add autonomous_agent coverage
- **Files changed**: 2 file(s)

**Changed files:**
- `agents/dependency_agent.py`
- `tests/test_autonomous_agents.py`

---

## f782cc6 — 2026-06-27 09:00 UTC

- **SHA**: `f782cc6a4792af9c968c2fe2420f481b158230ba`
- **Author**: GadgetAI
- **Message**: make repo public + SARIF cleanup + inventory update
- **Files changed**: 6 file(s)

**Changed files:**
- `.github/workflows/security_scan.yml`
- `.gitignore`
- `CLAUDE.md`
- `autonomous_agent/core/audit_logger.py`
- `docs/inventory/services.yaml`
- `tests/test_audit_logger.py`

---

## 8e2cd74 — 2026-06-24 05:31 UTC

- **SHA**: `8e2cd7439e3abefe4fdf418e268715c0059c7e96`
- **Author**: Gadget Lab
- **Message**: fix: resolve PR #153 lint blockers (E1123, E1101, W1514, W3101) (#167)
- **Files changed**: 45 file(s)

**Changed files:**
- `.github/scripts/ai_agent_main.py`
- `.github/scripts/ai_code_suggestor.py`
- `.github/scripts/async_parallel_analyzer.py`
- `.github/scripts/badge_generator.py`
- `.github/scripts/check_policy.py`
- `.github/scripts/complexity_reporter.py`
- `.github/scripts/copilot_integration.py`
- `.github/scripts/cot_selector.py`
- `.github/scripts/docgen.py`
- `.github/scripts/elite_copilot.py`
- `.github/scripts/error_handler.py`
- `.github/scripts/gather_context.py`
- `.github/scripts/generate_rollback_manifest.py`
- `.github/scripts/health_dashboard_generator.py`
- `.github/scripts/inline_pr_commenter.py`
- `.github/scripts/issue_auto_creator.py`
- `.github/scripts/metrics_collector.py`
- `.github/scripts/parallel_code_analyzer.py`
- `.github/scripts/performance_benchmark.py`
- `.github/scripts/pr_inline_commenter.py`

---

## 038024a — 2026-06-22 22:29 UTC

- **SHA**: `038024a5b220ced58c954cf90684a97acf23cb54`
- **Author**: GadgetAI
- **Message**: Add n8n workflow template index and n8n API key expiry monitor
- **Files changed**: 1 file(s)

**Changed files:**
- `n8n-templates/README.md`

---

## cd9ce7d — 2026-06-22 08:48 UTC

- **SHA**: `cd9ce7d12e373c6e5e499c56144d1913a0ff8af4`
- **Author**: GadgetAI
- **Message**: fix(ci): resolve all test failures blocking green CI
- **Files changed**: 5 file(s)

**Changed files:**
- `.github/scripts/generate_rollback_manifest.py`
- `autonomous_agent/core/audit_logger.py`
- `autonomous_agent/core/github_client.py`
- `pytest.ini`
- `tests/test_github_client_comprehensive.py`

---

## 4b135ce — 2026-06-22 06:27 UTC

- **SHA**: `4b135ceaace729bc520702f120db53ee4d9bcfb7`
- **Author**: GadgetAI
- **Message**: fix(ci): handle ENV_CONFLICT from Vercel API, pull --rebase before push in set-vercel-env
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/set-vercel-env.yml`

---

## 3fddcab — 2026-06-22 06:26 UTC

- **SHA**: `3fddcabc1b9dae26ec792e9a6ea57f054e337b50`
- **Author**: GadgetAI
- **Message**: fix(ci): fix YAML parse error in set-vercel-env (multiline python in block scalar)
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/set-vercel-env.yml`

---

## f9a1ffa — 2026-06-22 06:22 UTC

- **SHA**: `f9a1ffa142bb2633dfe2acab50695f447de67e99`
- **Author**: GadgetAI
- **Message**: fix(ci): correct noreply email in set-vercel-env, improve Vercel API response parsing
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/set-vercel-env.yml`

---

## 41beabf — 2026-06-22 06:03 UTC

- **SHA**: `41beabf2f006059ccd63884babe8bd1604397751`
- **Author**: GadgetAI
- **Message**: feat(dashboard): live pipeline status page
- **Files changed**: 3 file(s)

**Changed files:**
- `landing/app/api/dashboard/route.ts`
- `landing/app/dashboard/page.tsx`
- `landing/next-env.d.ts`

---

## 338d287 — 2026-06-21 06:35 UTC

- **SHA**: `338d2872507bdad415cf55663517bee8d21ef0f6`
- **Author**: GadgetAI
- **Message**: chore: add one-shot workflow to set Vercel env vars via API
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/set-vercel-env.yml`

---

## 7e141e1 — 2026-06-21 06:33 UTC

- **SHA**: `7e141e115f3648d66bd630cf81bdff57087773cb`
- **Author**: GadgetAI
- **Message**: feat: persistent scan pages, share button, shared scan lib
- **Files changed**: 4 file(s)

**Changed files:**
- `landing/app/api/scan/route.ts`
- `landing/app/scan/[owner]/[repo]/page.tsx`
- `landing/app/scanner/page.tsx`
- `landing/lib/scan.ts`

---

## 7aea7bc — 2026-06-21 06:12 UTC

- **SHA**: `7aea7bc48abcc8e97af66d9a98127124eafcaac4`
- **Author**: GadgetAI
- **Message**: fix(lint): move mid-file import to top in auto_pr.py, modernize ruff config
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/scripts/auto_pr.py`
- `pyproject.toml`

---

## ad2e102 — 2026-06-21 06:07 UTC

- **SHA**: `ad2e102f74a1c554396f8e922ea848776578acd2`
- **Author**: GadgetAI
- **Message**: style: reformat auto_pr.py and weekly_digest.py at line-length=88
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/scripts/auto_pr.py`
- `.github/scripts/weekly_digest.py`

---

## e20dbde — 2026-06-21 06:00 UTC

- **SHA**: `e20dbde9395dcc74c84d7a46e5be74bab1d42b5c`
- **Author**: GadgetAI
- **Message**: chore: update AI docs
- **Files changed**: 17 file(s)

**Changed files:**
- `Ai`
- `docs/create`
- `a`
- `autonomous`
- `fully`
- `structured`
- `and`
- `bulletpro`
- `(1).docx`
- `Ai`
- `docs/create`
- `a`
- `autonomous`
- `fully`
- `structured`
- `and`
- `bulletpro.docx`

---

## d57927c — 2026-06-21 05:59 UTC

- **SHA**: `d57927cd7f6de7ddcf057cdec2be81ad2200da91`
- **Author**: GadgetAI
- **Message**: style: black-format auto_pr.py and weekly_digest.py
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/scripts/auto_pr.py`
- `.github/scripts/weekly_digest.py`

---

## 271baa2 — 2026-06-21 05:57 UTC

- **SHA**: `271baa20d7890dd1a4ef6e45f6cba3bc5c61f38f`
- **Author**: GadgetAI
- **Message**: chore: ignore landing build artifacts, run artifacts, and mcp_server
- **Files changed**: 1 file(s)

**Changed files:**
- `.gitignore`

---

## e99313d — 2026-06-21 05:57 UTC

- **SHA**: `e99313deffdd511777960aa972f06d7f4781e140`
- **Author**: GadgetAI
- **Message**: feat: add SaaS growth features — scanner, badge API, auto-PR, weekly digest
- **Files changed**: 10 file(s)

**Changed files:**
- `.github/scripts/auto_pr.py`
- `.github/scripts/weekly_digest.py`
- `.github/workflows/auto-pr.yml`
- `.github/workflows/repository-overseer.yml`
- `README.md`
- `landing/app/api/badge/[owner]/[repo]/route.ts`
- `landing/app/api/scan/route.ts`
- `landing/app/api/slack/command/route.ts`
- `landing/app/scanner/page.tsx`
- `landing/lib/scan-types.ts`

---

## 2e44420 — 2026-06-21 05:50 UTC

- **SHA**: `2e444201c984959fabc8db3725cc381c713191be`
- **Author**: GadgetAI
- **Message**: style: black-format AuditLogger __init__ signature
- **Files changed**: 1 file(s)

**Changed files:**
- `core/audit_logger.py`

---

## 74ba660 — 2026-06-21 05:48 UTC

- **SHA**: `74ba660cb904a1afdfb3d4c18550cc62d3b7367c`
- **Author**: GadgetAI
- **Message**: fix(ci): add scikit-learn + psutil deps, fix AuditLogger log_dir signature
- **Files changed**: 2 file(s)

**Changed files:**
- `core/audit_logger.py`
- `requirements.txt`

---

## 575d201 — 2026-06-21 05:45 UTC

- **SHA**: `575d20129d11335b83651bf0bdd53a4e97872c03`
- **Author**: GadgetAI
- **Message**: fix(pre-commit): remove extra trailing newline from bulletpro.md
- **Files changed**: 8 file(s)

**Changed files:**
- `Ai`
- `docs/create`
- `a`
- `autonomous`
- `fully`
- `structured`
- `and`
- `bulletpro.md`

---

## 43caa34 — 2026-06-21 05:42 UTC

- **SHA**: `43caa34a986c00c3277b236c3b032a1e3f69bf4f`
- **Author**: GadgetAI
- **Message**: fix(pre-commit): add missing trailing newlines to Ai docs text files
- **Files changed**: 48 file(s)

**Changed files:**
- `Ai`
- `docs/1.`
- `AI-Powered`
- `Circular-as-a-Service.txt`
- `Ai`
- `docs/1.`
- `How`
- `can`
- `we`
- `optimize`
- `the`
- `AI`
- `model.txt`
- `Ai`
- `docs/Perplexity`
- `buss.html`
- `Ai`
- `docs/Perplexity`
- `github.html`
- `Ai`

---

## 0911ff7 — 2026-06-21 05:41 UTC

- **SHA**: `0911ff77c69523574af06b82bf85afff70589ee2`
- **Author**: GadgetAI
- **Message**: fix(ci): strip trailing whitespace, add numpy + pytest-asyncio deps
- **Files changed**: 70 file(s)

**Changed files:**
- `.env.example`
- `.env.txt`
- `.github/workflows/code-quality-optimized.yml`
- `.github/workflows/repository-overseer.yml`
- `.gitignore`
- `00_READ_ME_FIRST.md`
- `CONFIGURE_TOKENS.txt`
- `CONFIGURE_WIZARD.bat`
- `CONTRIBUTING.md`
- `CORRECT_INSTALL_COMMANDS.txt`
- `DEPLOYMENT.md`
- `DIAGNOSE.bat`
- `DOUBLE_CLICK_ME.bat`
- `FINAL_INSTALL.py`
- `FIX_NOW.txt`
- `HOW_TO_RUN.md`
- `INLINE_INSTALL.py`
- `INSTALL.md`
- `INSTALLATION_RUNNER.py`
- `INSTALLATION_SETUP_COMPLETE.md`

---

## fcf0bd3 — 2026-06-21 05:39 UTC

- **SHA**: `fcf0bd3bd54c8913431bb2fc5a2aa2a9e7aff9b8`
- **Author**: GadgetAI
- **Message**: fix(pre-commit): strip trailing whitespace from all tracked text files
- **Files changed**: 28 file(s)

**Changed files:**
- `Ai`
- `docs/Perplexity`
- `buss_files/index-AO5YUTXc.js.download`
- `Ai`
- `docs/Perplexity`
- `github.html`
- `Ai`
- `docs/Perplexity`
- `github_files/index-D_VLSpJ3.js.download`
- `Ai`
- `docs/Perplexity`
- `new_files/index-D_VLSpJ3.js.download`
- `CLICK_ME_TO_INSTALL.txt`
- `EXECUTION_REPORT.md`
- `HOW_TO_GET_TOKENS.txt`
- `INDEX.txt`
- `INSTALLATION_COMPLETE_SUMMARY.txt`
- `INSTALLATION_INSTRUCTIONS.md`
- `INSTALLATION_REPORT.md`
- `PRE_INSTALLATION_CHECKLIST.txt`

---

## fd31a49 — 2026-06-21 05:35 UTC

- **SHA**: `fd31a499d2c39ed83b3dfcbcf611b63d8bc9af42`
- **Author**: GadgetAI
- **Message**: fix(pre-commit): strip trailing whitespace from TEST_COVERAGE_REPORT.md
- **Files changed**: 1 file(s)

**Changed files:**
- `TEST_COVERAGE_REPORT.md`

---

## ce4973a — 2026-06-21 05:34 UTC

- **SHA**: `ce4973a8d67b020b74af668a68c58a2ffe827ae0`
- **Author**: GadgetAI
- **Message**: chore: commit auto-generated changelog workflow and README badge update
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/workflows/changelog.yml`
- `README.md`

---

## 0057f41 — 2026-06-21 05:34 UTC

- **SHA**: `0057f410b9d1fa630bbc7d7baf3c90c035f25dd1`
- **Author**: GadgetAI
- **Message**: fix(ci): fix YAML syntax error in code-quality-optimized.yml
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`

---

## 628374e — 2026-06-21 05:32 UTC

- **SHA**: `628374ee4356f408835be7bab6d739fe72597149`
- **Author**: GadgetAI
- **Message**: fix(ci): add pytest-asyncio and suppress mypy import-untyped errors
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/workflows/ai_agent_workflow.yml`
- `pyproject.toml`

---

## ed71e0a — 2026-06-21 05:31 UTC

- **SHA**: `ed71e0a1d3ba9307e40add3dcc59ec23098a264d`
- **Author**: GadgetAI
- **Message**: fix(types): suppress Redis assignment type mismatch in message_queue
- **Files changed**: 1 file(s)

**Changed files:**
- `core/message_queue.py`

---

## 05abf04 — 2026-06-21 05:30 UTC

- **SHA**: `05abf0480946612010b40307aef47370cea2c6e0`
- **Author**: GadgetAI
- **Message**: fix(pre-commit): add types-PyYAML and types-redis to mypy hook deps
- **Files changed**: 1 file(s)

**Changed files:**
- `.pre-commit-config.yaml`

---

## e8db9de — 2026-06-21 05:27 UTC

- **SHA**: `e8db9de7ad65706a4523ee020f5785cbd22de646`
- **Author**: GadgetAI
- **Message**: fix(mypy): add ignore_missing_imports = true to suppress import-untyped errors
- **Files changed**: 1 file(s)

**Changed files:**
- `pyproject.toml`

---

## ebdebed — 2026-06-21 05:25 UTC

- **SHA**: `ebdebed7604e498dc54b0e1c68fa0c2c9ad806ee`
- **Author**: GadgetAI
- **Message**: fix(types): resolve all mypy errors — add overrides + targeted fixes
- **Files changed**: 6 file(s)

**Changed files:**
- `agents/dependency_agent.py`
- `agents/triage_agent.py`
- `autopilot/__init__.py`
- `autopilot/ai_optimization/ml_priority_scorer.py`
- `core/github_client.py`
- `pyproject.toml`

---

## 2f5d243 — 2026-06-21 05:18 UTC

- **SHA**: `2f5d2436ddd7a40b88703e6d48cca07e2d803f10`
- **Author**: GadgetAI
- **Message**: fix(lint): resolve all remaining ruff errors across repo
- **Files changed**: 8 file(s)

**Changed files:**
- `autonomous_agent/agents/security_scanner.py`
- `autonomous_agent/agents/workflow_optimizer.py`
- `autonomous_agent/core/audit_logger.py`
- `autonomous_agent/core/orchestrator.py`
- `autopilot/ai_optimization/intelligent_cache.py`
- `autopilot/ai_optimization/ml_priority_scorer.py`
- `core/risk_scorer.py`
- `pyproject.toml`

---

## f3fdc52 — 2026-06-21 05:13 UTC

- **SHA**: `f3fdc522f0397cbd4e211b4719ad6a9d1cfdd28a`
- **Author**: GadgetAI
- **Message**: style: ruff auto-fix + whitespace cleanup across repo
- **Files changed**: 43 file(s)

**Changed files:**
- `.github/scripts/generate_rollback_manifest.py`
- `.github/scripts/parallel_code_analyzer_optimized.py`
- `Ai`
- `docs/config.py`
- `FINAL_INSTALL.py`
- `INLINE_INSTALL.py`
- `INSTALLATION_RUNNER.py`
- `RUN_INSTALLATION.py`
- `TEST_ENVIRONMENT.py`
- `autonomous_agent/__init__.py`
- `autonomous_agent/agents/branch_manager.py`
- `autonomous_agent/agents/code_reviewer.py`
- `autonomous_agent/agents/documentation_generator.py`
- `autonomous_agent/agents/health_monitor.py`
- `autonomous_agent/agents/issue_manager.py`
- `autonomous_agent/agents/security_scanner.py`
- `autonomous_agent/agents/workflow_optimizer.py`
- `autonomous_agent/cli.py`
- `autonomous_agent/core/audit_logger.py`
- `autonomous_agent/core/base_agent.py`

---

## 00b8b19 — 2026-06-21 05:07 UTC

- **SHA**: `00b8b1968fd1c3ff5c51ec70883e18975e298aa5`
- **Author**: GadgetAI
- **Message**: style: black 24.4.2 formatting on pre-existing setup scripts
- **Files changed**: 18 file(s)

**Changed files:**
- `Ai`
- `docs/config.py`
- `FINAL_INSTALL.py`
- `INLINE_INSTALL.py`
- `INSTALLATION_RUNNER.py`
- `RUN_INSTALLATION.py`
- `TEST_ENVIRONMENT.py`
- `create_agents.py`
- `create_cli.py`
- `create_core_files.py`
- `direct_install.py`
- `execute_install.py`
- `install.py`
- `master_install.py`
- `quick_setup.py`
- `run_all_steps.py`
- `test_env.py`
- `verify_installation.py`

---

## 1518faf — 2026-06-21 04:59 UTC

- **SHA**: `1518faf4762cce16e7b772434d21d9f59c0ce386`
- **Author**: GadgetAI
- **Message**: style: reformat with black 24.4.2 to match pre-commit CI version
- **Files changed**: 3 file(s)

**Changed files:**
- `.github/scripts/health_dashboard_generator.py`
- `.github/scripts/pr_triage.py`
- `tests/unit/test_health_dashboard_generator.py`

---

## d663b89 — 2026-06-21 04:54 UTC

- **SHA**: `d663b89f0a4b0e0acacc013bb17cea165e0c206a`
- **Author**: GadgetAI
- **Message**: style: black + ruff formatting fixes for pr_triage and health_dashboard
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/scripts/health_dashboard_generator.py`
- `.github/scripts/pr_triage.py`

---

## 1d9efbb — 2026-06-21 04:52 UTC

- **SHA**: `1d9efbb9b48edcd8b07bb6a8011ea7b05170b698`
- **Author**: GadgetAI
- **Message**: feat(dashboard): implement generate_html_dashboard() with Chart.js
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/scripts/health_dashboard_generator.py`
- `tests/unit/test_health_dashboard_generator.py`

---

## 72aafb7 — 2026-06-21 04:41 UTC

- **SHA**: `72aafb79e1bfe6841b69409526ba39790d13d94b`
- **Author**: GadgetAI
- **Message**: feat(triage): add PR triage pipeline
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/scripts/pr_triage.py`
- `.github/workflows/pr-triage.yml`

---

## 65306b7 — 2026-06-21 03:51 UTC

- **SHA**: `65306b78e7e0047d2c5b7edc8e60c18d7a19dc11`
- **Author**: GadgetAI
- **Message**: fix(autopilot): fix rate limit API for PyGithub 2.x
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/workflows/elite_copilot.yml`
- `autopilot/autopilot.py`

---

## daeefe1 — 2026-06-21 03:49 UTC

- **SHA**: `daeefe12fe2b5792c4e582e897e44b886564d5c0`
- **Author**: GadgetAI
- **Message**: fix(autopilot): use GH_PAT for cross-repo access; fix GET /user 403
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/workflows/elite_copilot.yml`
- `autopilot/autopilot.py`

---

## 5edaadd — 2026-06-20 23:41 UTC

- **SHA**: `5edaadd6b3457b0257a15dd771edaeaf96cb90bf`
- **Author**: GadgetAI
- **Message**: fix: show £199 GBP on landing page pricing
- **Files changed**: 1 file(s)

**Changed files:**
- `landing/app/page.tsx`

---

## 0482496 — 2026-06-20 07:01 UTC

- **SHA**: `0482496720d42195f4a66f0a0d39038be9794b0a`
- **Author**: GadgetAI
- **Message**: feat(agents): add subagent fan-out — code review, security, dependency, triage + dispatch
- **Files changed**: 32 file(s)

**Changed files:**
- `.github/workflows/ai_agent_workflow.yml`
- `.github/workflows/subagent-dispatch.yml`
- `agents/code_review_agent.py`
- `agents/dependency_agent.py`
- `agents/security_scan_agent.py`
- `agents/triage_agent.py`
- `autonomous_agent/agents/__init__.py`
- `autonomous_agent/agents/branch_manager.py`
- `autonomous_agent/agents/code_reviewer.py`
- `autonomous_agent/agents/documentation_generator.py`
- `autonomous_agent/agents/health_monitor.py`
- `autonomous_agent/agents/issue_manager.py`
- `autonomous_agent/agents/security_scanner.py`
- `autonomous_agent/agents/workflow_optimizer.py`
- `autonomous_agent/cli.py`
- `autonomous_agent/core/__init__.py`
- `autonomous_agent/core/audit_logger.py`
- `autonomous_agent/core/base_agent.py`
- `autonomous_agent/core/config.py`
- `autonomous_agent/core/github_client.py`

---

## 3093f4f — 2026-06-20 06:14 UTC

- **SHA**: `3093f4faa2a352811cc516fc2f33cee3799de7d7`
- **Author**: GadgetAI
- **Message**: fix(ci): resolve yamllint gate and pytest dependency failures
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`
- `.yamllint`

---

## b9ab983 — 2026-06-20 05:18 UTC

- **SHA**: `b9ab983cadf5a42b40b8f748375a121a4014a8f2`
- **Author**: Gadget Lab
- **Message**: fix: add .yamllint.yml to silence pre-commit-ci gate noise
- **Files changed**: 1 file(s)

**Changed files:**
- `.yamllint.yml`

---

## c8aca75 — 2026-06-20 05:14 UTC

- **SHA**: `c8aca7501c3c821cc324cae7d6d9589f63e03547`
- **Author**: GadgetAI
- **Message**: fix(autopilot): add preflight diagnostics and zero-repos circuit breaker
- **Files changed**: 3 file(s)

**Changed files:**
- `.github/workflows/elite_copilot.yml`
- `autopilot/autopilot.py`
- `pyproject.toml`

---

## d4f602b — 2026-06-20 04:24 UTC

- **SHA**: `d4f602bfc0368e5c18e63c38297b696208036feb`
- **Author**: Gadget Lab
- **Message**: Update dependencies to include pytest and coverage tools
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/code-quality-optimized.yml`

---

## 67a3461 — 2026-06-19 08:32 UTC

- **SHA**: `67a3461ebd9470be779b61e8e7fe42c91eeaa23e`
- **Author**: GadgetAI
- **Message**: fix(landing): un-ignore landing/lib/ and add db.ts
- **Files changed**: 2 file(s)

**Changed files:**
- `.gitignore`
- `landing/lib/db.ts`

---

## c944766 — 2026-06-19 08:27 UTC

- **SHA**: `c9447663abad26bfc5bb18319f4f51709ae30560`
- **Author**: GadgetAI
- **Message**: fix(landing): regenerate package-lock.json with @vercel/postgres deps
- **Files changed**: 1 file(s)

**Changed files:**
- `landing/package-lock.json`

---

## b3d06e8 — 2026-06-19 08:25 UTC

- **SHA**: `b3d06e824185a010282ba3d6089c91a6e831d09a`
- **Author**: GadgetAI
- **Message**: feat(landing): wire Stripe + Postgres into webhook handler
- **Files changed**: 6 file(s)

**Changed files:**
- `landing/.env.example`
- `landing/.gitignore`
- `landing/app/api/stripe/webhook/route.ts`
- `landing/app/dashboard/page.tsx`
- `landing/app/success/page.tsx`
- `landing/package.json`

---

## c992edd — 2026-06-19 06:32 UTC

- **SHA**: `c992eddca525defd9ad5b293864635e887df1c06`
- **Author**: labgadget015-dotcom
- **Message**: Merge remote-tracking branch 'origin/main'
- **Files changed**: 0 file(s)

---

## 593a649 — 2026-06-19 05:55 UTC

- **SHA**: `593a64900c4023c40aca8e34b6dae9173ff36ad1`
- **Author**: labgadget015-dotcom
- **Message**: Merge remote-tracking branch 'origin/main'
- **Files changed**: 0 file(s)

---

## 3f5f47b — 2026-06-17 06:08 UTC

- **SHA**: `3f5f47b9947828a34ad8e42eea219789f0435603`
- **Author**: GadgetAI
- **Message**: fix: allow workflow_dispatch to trigger production deploy
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/deploy-landing.yml`

---

## 323452b — 2026-06-17 05:45 UTC

- **SHA**: `323452b2743448aa29b4716cc6d11b60c8c18d4f`
- **Author**: GadgetAI
- **Message**: fix: initialize Stripe lazily to avoid build-time crash
- **Files changed**: 1 file(s)

**Changed files:**
- `landing/app/api/stripe/webhook/route.ts`

---

## f85f494 — 2026-06-17 05:44 UTC

- **SHA**: `f85f4941df48175d5b4f3c7ab98b475a95abf902`
- **Author**: GadgetAI
- **Message**: fix: use stripe API version supported by stripe@17.7.0
- **Files changed**: 1 file(s)

**Changed files:**
- `landing/app/api/stripe/webhook/route.ts`

---

## 1ab640b — 2026-06-17 05:42 UTC

- **SHA**: `1ab640b2dfdb2ba0fa30808099b63fc85d125d37`
- **Author**: GadgetAI
- **Message**: fix: add .eslintrc.json to skip interactive ESLint setup in CI
- **Files changed**: 1 file(s)

**Changed files:**
- `landing/.eslintrc.json`

---

## 24831fc — 2026-06-17 05:41 UTC

- **SHA**: `24831fc483d68829cfc5863ade31d65c72a27d6f`
- **Author**: GadgetAI
- **Message**: fix: add package-lock.json for landing page CI cache
- **Files changed**: 1 file(s)

**Changed files:**
- `landing/package-lock.json`

---

## 8a6563a — 2026-06-17 05:39 UTC

- **SHA**: `8a6563a308deaa475055c8497eacf6796bdf2831`
- **Author**: GadgetAI
- **Message**: feat: scaffold SaaS landing page, Stripe webhook handler, and Vercel deploy pipeline
- **Files changed**: 13 file(s)

**Changed files:**
- `.github/copilot-instructions.md`
- `.github/workflows/deploy-landing.yml`
- `docs/REVENUE_ROADMAP.md`
- `landing/.env.example`
- `landing/app/api/stripe/webhook/route.ts`
- `landing/app/globals.css`
- `landing/app/layout.tsx`
- `landing/app/page.tsx`
- `landing/package.json`
- `landing/postcss.config.js`
- `landing/tailwind.config.ts`
- `landing/tsconfig.json`
- `landing/vercel.json`

---

## 8de8b7b — 2026-06-17 03:59 UTC

- **SHA**: `8de8b7b9daa67d312d5e0867ac2a12c9c907c959`
- **Author**: GadgetAI
- **Message**: fix: remove .github/scripts from pytest coverage scope
- **Files changed**: 1 file(s)

**Changed files:**
- `pytest.ini`

---

## 1497c06 — 2026-06-17 03:41 UTC

- **SHA**: `1497c062be3bc42feefa15c2c5cda7a9e76e011a`
- **Author**: GadgetAI
- **Message**: fix: harden gitleaks config and downgrade action to v2
- **Files changed**: 2 file(s)

**Changed files:**
- `.github/workflows/security_scan.yml`
- `.gitleaks.toml`

---

## a6ba365 — 2026-06-17 03:39 UTC

- **SHA**: `a6ba365553917da6cbde60b5b7fc05270e31c0a9`
- **Author**: Claude
- **Message**: feat(aria): DRC follow-up — LLM cost gate, visible spend widget, Promise.allSettled
- **Files changed**: 1 file(s)

**Changed files:**
- `docs/aria-v3-p2.html`

---

## eb36d1f — 2026-06-17 03:32 UTC

- **SHA**: `eb36d1f0495c47e1b2c3cd4e4d26ca30c9ff6e59`
- **Author**: GadgetAI
- **Message**: chore: align pytest coverage threshold with pyproject.toml
- **Files changed**: 1 file(s)

**Changed files:**
- `pytest.ini`

---

## 5827c38 — 2026-06-14 08:22 UTC

- **SHA**: `5827c38a1f23963525596184886fbfa70abc382a`
- **Author**: GadgetAI
- **Message**: chore: add upper-bound pins to CI-impacting dependencies
- **Files changed**: 1 file(s)

**Changed files:**
- `requirements.txt`

---

## 54f8e75 — 2026-06-14 07:37 UTC

- **SHA**: `54f8e75cf9298f5826903c0eeadb88b260d69cae`
- **Author**: GadgetAI
- **Message**: fix: add pytest-timeout to resolve strict-config unknown option error
- **Files changed**: 1 file(s)

**Changed files:**
- `requirements.txt`

---

## 4762c41 — 2026-06-14 06:30 UTC

- **SHA**: `4762c4179a0b50c50b73c638f966b2012d61f8b3`
- **Author**: GadgetAI
- **Message**: fix: pin pytest-asyncio<1.0.0 to prevent broken test collection
- **Files changed**: 2 file(s)

**Changed files:**
- `pytest.ini`
- `requirements.txt`

---

## ea88faa — 2026-06-13 06:40 UTC

- **SHA**: `ea88faaac9cc6fadb604decdf124e972ff7f17eb`
- **Author**: GadgetAI
- **Message**: fix: add .github/labeler.yml to resolve Auto Label CI failure
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/labeler.yml`

---

## 9c1c2d7 — 2026-06-13 06:18 UTC

- **SHA**: `9c1c2d7d0a87c90c10fefa57b9c104dd6187eec1`
- **Author**: Gadget Lab
- **Message**: fix: bump actions to Node 24 runtimes and fix daily summary path (#147)
- **Files changed**: 21 file(s)

**Changed files:**
- `.github/scripts/deployment-automation.sh`
- `.github/workflows/agent_dispatcher.yml`
- `.github/workflows/ai_agent_workflow.yml`
- `.github/workflows/branch_protection.yml`
- `.github/workflows/code-quality-optimized.yml`
- `.github/workflows/dry_run_gate.yml`
- `.github/workflows/elite_copilot.yml`
- `.github/workflows/monitoring_export.yml`
- `.github/workflows/pre-commit-ci.yml`
- `.github/workflows/release-and-publish.yml`
- `.github/workflows/repository-overseer.yml`
- `.github/workflows/security_scan.yml`
- `.github/workflows/test_metrics.yml`
- `.gitleaks.toml`
- `autopilot/autopilot.py`
- `scripts/automation/create-release.sh`
- `scripts/automation/lint-code.sh`
- `scripts/automation/setup-dev-env.sh`
- `scripts/automation/setup_python.sh`
- `scripts/setup-dev.sh`

---

## 4768dab — 2026-06-04 06:45 UTC

- **SHA**: `4768dab1a3b65a9a42120512ef38e39a6ea008e1`
- **Author**: GadgetAI
- **Message**: fix: correct CoT selector import in ai_agent_workflow
- **Files changed**: 1 file(s)

**Changed files:**
- `.github/workflows/ai_agent_workflow.yml`

---

## c2a49c8 — 2026-06-04 06:40 UTC

- **SHA**: `c2a49c82e04b0d6310a6ae65746ddf4583933524`
- **Author**: GadgetAI
- **Message**: fix: wrap blocking LLM calls in asyncio.to_thread and remove pre-call rate limiting
- **Files changed**: 2 file(s)

**Changed files:**
- `core/github_client.py`
- `core/llm_provider.py`

---

## 2b5eb86 — 2026-06-04 06:28 UTC

- **SHA**: `2b5eb8622329b09d89b4bae96130ba1df2c1c3b9`
- **Author**: GadgetAI
- **Message**: docs: improve CLAUDE.md with venv setup, test layout, and coverage clarifications
- **Files changed**: 1 file(s)

**Changed files:**
- `CLAUDE.md`

---

## c2eb0de — 2026-06-02 06:59 UTC

- **SHA**: `c2eb0de8f5ed9aeb80db791655c53ef49873124d`
- **Author**: GadgetAI
- **Message**: docs: update CLAUDE.md with action.yml, context.json, and Slack node fix
- **Files changed**: 1 file(s)

**Changed files:**
- `CLAUDE.md`

---

## 5aec882 — 2026-05-09 06:31 UTC

- **SHA**: `5aec88275b36c7b53022269aec5d9a7473f1251e`
- **Author**: Gadget Lab
- **Message**: Merge pull request #120 from labgadget015-dotcom/copilot/fix-inline-pr-risk-scoring
- **Files changed**: 0 file(s)

---

## 0b6bb65 — 2026-05-08 11:51 UTC

- **SHA**: `0b6bb65f706e7bc6fe99be33f6336fb6c8b77723`
- **Author**: Gadget Lab
- **Message**: ok
- **Files changed**: 1 file(s)

**Changed files:**
- `.bandit`

---

## 6f85fc8 — 2026-05-08 11:14 UTC

- **SHA**: `6f85fc8528f210f44ceb9eb21e9185be0e3470fa`
- **Author**: GadgetAI
- **Message**: fix: resolve markdownlint violations (MD012, MD018, MD019)
- **Files changed**: 7 file(s)

**Changed files:**
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `DEPLOYMENT_CODE_SUGGESTIONS.md`
- `README.md`
- `docs/CHANGELOG.md`
- `docs/CONSOLIDATION_ROADMAP.md`
- `docs/PRODUCT_HUNT_LAUNCH.md`

---

## 002bad8 — 2026-05-08 11:09 UTC

- **SHA**: `002bad8f1154f5a8db6a1d1954d7c0b8d96d2478`
- **Author**: GadgetAI
- **Message**: fix: narrow markdownlint rules to prevent CI auto-fix failures
- **Files changed**: 2 file(s)

**Changed files:**
- `.markdownlint.json`
- `.pre-commit-config.yaml`

---

## e203d4d — 2026-05-08 10:14 UTC

- **SHA**: `e203d4db9f9b63f6e67b9c691566aad0e3a5ea54`
- **Author**: GadgetAI
- **Message**: fix: add markdownlint config to disable rules that fail on auto-generated docs
- **Files changed**: 1 file(s)

**Changed files:**
- `.markdownlint.json`

---

## c2af2c8 — 2026-05-08 10:11 UTC

- **SHA**: `c2af2c8d622da1c26b22e26cf9a4aefd1a3ba48b`
- **Author**: GadgetAI
- **Message**: fix: add detect-secrets baseline required by pre-commit hook
- **Files changed**: 1 file(s)

**Changed files:**
- `.secrets.baseline`

---

## 237059c — 2026-05-08 09:43 UTC

- **SHA**: `237059cd1885795f080126490bd1b350880cfb48`
- **Author**: GadgetAI
- **Message**: fix: remove duplicate jsonData key in grafana-datasources.yml
- **Files changed**: 1 file(s)

**Changed files:**
- `monitoring/grafana-datasources.yml`

---

## e000cfa — 2026-05-08 09:39 UTC

- **SHA**: `e000cfa6cb9977b5f40f71aefe07c097ef0af309`
- **Author**: GadgetAI
- **Message**: fix: add missing .yamllint config required by pre-commit yamllint hook
- **Files changed**: 1 file(s)

**Changed files:**
- `.yamllint`

---

## 78157c2 — 2026-05-08 09:36 UTC

- **SHA**: `78157c2379e3bc4812ec1b6ae666fc4c169eeeed`
- **Author**: GadgetAI
- **Message**: fix: restrict no-commit-to-branch hook to pre-push stage
- **Files changed**: 1 file(s)

**Changed files:**
- `.pre-commit-config.yaml`

---

## a21528c — 2026-05-08 09:33 UTC

- **SHA**: `a21528cda6910b9b55150de270109808706e7eb4`
- **Author**: GadgetAI
- **Message**: fix: exclude .vscode/settings.json from check-json (uses JSONC)
- **Files changed**: 1 file(s)

**Changed files:**
- `.pre-commit-config.yaml`

---

## 95aa060 — 2026-05-08 09:30 UTC

- **SHA**: `95aa0609eaed70d405e43853e5d501cfc7e46dc4`
- **Author**: GadgetAI
- **Message**: style: ensure all files end with a newline
- **Files changed**: 19 file(s)

**Changed files:**
- `.benchmark_results/benchmark_20260124_065337.json`
- `.benchmark_results/benchmark_20260124_065410.json`
- `.benchmark_results/benchmark_20260128_053038.json`
- `.vscode/extensions.json`
- `.workflow_history.json`
- `CONTRIBUTING_GENERATED.md`
- `COPILOT_INTEGRATION_REPORT.md`
- `ai-optimization-report.json`
- `analysis-results.json`
- `copilot_integration_results.json`
- `docs/API_REFERENCE.md`
- `docs/CHANGELOG.md`
- `docs/CONTRIBUTING_GENERATED.md`
- `docs/FINAL_DEPLOYMENT_STATUS.md`
- `docs/ROLLBACK.md`
- `docs/USER_GUIDE.md`
- `integration-test-results.json`
- `requirements.txt`
- `scripts/automation/README.md`

---

## cb01fcd — 2026-05-08 09:25 UTC

- **SHA**: `cb01fcd891be8ee181ac1917ac9fd3ed4b342aa5`
- **Author**: GadgetAI
- **Message**: style: strip trailing whitespace from hidden dirs and config files
- **Files changed**: 32 file(s)

**Changed files:**
- `.bandit`
- `.coveragerc`
- `.devcontainer/devcontainer.json`
- `.github/CI-CD-IMPLEMENTATION-SUMMARY.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/ISSUE_TEMPLATE/uaip-config.yml`
- `.github/QUICK-START-GUIDE.md`
- `.github/config/analysis-config.yml`
- `.github/config/grafana-dashboard.json`
- `.github/config/policy.yml`
- `.github/config/prometheus.yml`
- `.github/scripts/cost_calculator.py`
- `.github/scripts/deployment-automation.sh`
- `.github/scripts/health_dashboard_generator.py`
- `.github/scripts/inline_pr_commenter.py`
- `.github/scripts/issue_auto_creator.py`
- `.github/scripts/parallel_code_analyzer.py`
- `.github/scripts/threshold_monitor.py`
- `.github/workflows/ai_agent_workflow.yml`

---

## 59847a4 — 2026-05-08 09:19 UTC

- **SHA**: `59847a4c14eb6ae073f89d3153aeb44d04c7d1df`
- **Author**: GadgetAI
- **Message**: style: strip trailing whitespace from all text files
- **Files changed**: 60 file(s)

**Changed files:**
- `ADVANCED_FEATURES_GUIDE.md`
- `CHANGES_SUMMARY.md`
- `DEPLOYMENT_MANIFEST.md`
- `DEPLOYMENT_SUCCESS.md`
- `ENHANCEMENT_REPORT.md`
- `EXECUTION_LOG.md`
- `FINAL_VERIFICATION_COMPLETE.md`
- `IMPLEMENTATION_FINAL_REPORT.md`
- `OVERSEER_COMPLETE_SUMMARY.md`
- `PROJECT_STATUS.md`
- `README.md`
- `SAVE_COMPLETE.md`
- `WHAT_NOW.md`
- `action.yml`
- `autopilot/config.yaml`
- `config/agent_config.yaml`
- `config/code_standards.yaml`
- `docker-compose.prod.yml`
- `docker-compose.yml`
- `docs/ADVANCED_FEATURES.md`

---

## 3381982 — 2026-05-08 09:11 UTC

- **SHA**: `33819821a48c7b6cf98d68e6e994d549cf731771`
- **Author**: GadgetAI
- **Message**: fix: add dict[str, Any] annotations throughout overseer/ to resolve mypy attr-defined errors
- **Files changed**: 4 file(s)

**Changed files:**
- `core/github_client.py`
- `overseer/doc_generator.py`
- `overseer/monitor.py`
- `overseer/orchestrator.py`

---

## e8ee387 — 2026-05-08 08:58 UTC

- **SHA**: `e8ee3875bc278652317e062a28ae95cec3c99c6a`
- **Author**: GadgetAI
- **Message**: fix: resolve mypy type errors in overseer/ core/ autopilot/
- **Files changed**: 9 file(s)

**Changed files:**
- `autopilot/ai_optimization/anomaly_detector.py`
- `core/policy_engine.py`
- `overseer/automation_engine.py`
- `overseer/cicd_optimizer.py`
- `overseer/code_analyzer.py`
- `overseer/dependency_manager.py`
- `overseer/doc_generator.py`
- `overseer/issue_triager.py`
- `overseer/monitor.py`

---

## 7c42be3 — 2026-05-08 08:53 UTC

- **SHA**: `7c42be37592faafb4b63ad47dd1cbfad0cf6087b`
- **Author**: Gadget Lab
- **Message**: Merge pull request #119 from labgadget015-dotcom/copilot/improve-test-coverage
- **Files changed**: 0 file(s)

---

## 10bd1e3 — 2026-05-08 08:46 UTC

- **SHA**: `10bd1e35f9ec628b326a3183b40dd06da37211c6`
- **Author**: GadgetAI
- **Message**: fix: add explicit mypy targets when pass_filenames=false
- **Files changed**: 1 file(s)

**Changed files:**
- `.pre-commit-config.yaml`

---

## 0bbe948 — 2026-05-08 08:43 UTC

- **SHA**: `0bbe9489ae2d6cbe9ce347198d4b6a5296807cbf`
- **Author**: GadgetAI
- **Message**: fix: resolve mypy errors in overseer and scripts
- **Files changed**: 4 file(s)

**Changed files:**
- `.github/scripts/llm_router.py`
- `.pre-commit-config.yaml`
- `overseer/monitor.py`
- `pyproject.toml`

---

## ab800b3 — 2026-05-08 08:37 UTC

- **SHA**: `ab800b3ed9a2636fb331914b29b63f489e2506bf`
- **Author**: GadgetAI
- **Message**: fix: suppress mypy import-untyped and double-module errors
- **Files changed**: 1 file(s)

**Changed files:**
- `pyproject.toml`

---

## 1326dc0 — 2026-05-08 08:33 UTC

- **SHA**: `1326dc0ce900febccbce1ccdac89f8732dd95f13`
- **Author**: GadgetAI
- **Message**: style: reformat 3 files missed by black after ruff edits
- **Files changed**: 3 file(s)

**Changed files:**
- `.github/scripts/performance_benchmark.py`
- `overseer/dependency_manager.py`
- `scripts/escalate_quality_issues.py`

---

## 2948624 — 2026-05-08 08:29 UTC

- **SHA**: `29486248cdd128ad13ced428bfe48827f3fe3e8c`
- **Author**: GadgetAI
- **Message**: fix: resolve all ruff violations to pass pre-commit CI
- **Files changed**: 115 file(s)

**Changed files:**
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
- `.github/scripts/elite_copilot.py`
- `.github/scripts/error_handler.py`
- `.github/scripts/gather_context.py`
- `.github/scripts/generate_rollback_manifest.py`
- `.github/scripts/health_dashboard_generator.py`
- `.github/scripts/inline_pr_commenter.py`
- `.github/scripts/issue_auto_creator.py`
- `.github/scripts/llm_router.py`

---

## 22527de — 2026-05-08 08:06 UTC

- **SHA**: `22527dedc0668e7c4fd854848dd6c259158cd0be`
- **Author**: GadgetAI
- **Message**: style: reformat 2 test files to match black 24.4.2 (pre-commit version)
- **Files changed**: 2 file(s)

**Changed files:**
- `tests/test_elite_copilot.py`
- `tests/test_overseer.py`

---

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
