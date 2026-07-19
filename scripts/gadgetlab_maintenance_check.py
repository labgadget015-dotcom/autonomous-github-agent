#!/usr/bin/env python3
"""GadgetLab Agent maintenance watchdog — REPORT ONLY, never mutates anything.

Runs weekly via Hermes cron, delivers to Telegram (8834644752).
Catches the things that silently rot in a human-gated-agent system:
  1. Local LLM routing broken (Ollama down / wrong default URL) -> paid cloud leak
  2. Guardrail drift (risk scorer / router classify behavior changed)
  3. Credential clocks (PAT expiry 2027-05-07, DRC token rotation age)
  4. SCALE guardrails (cost cap / rate limit drifted upward -> unbounded-cost risk)
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date

REPO = "/home/ai/autonomous-github-agent"
OLLAMA_URL = "http://localhost:11434/api/tags"
PAT_EXPIRY = date(2027, 5, 7)
DRC_LAST = date(2026, 7, 6)
# Scale ceilings that must NOT be lifted without review (Vision II: bounded scale).
COST_CAP_MAX = 1.0
OP_LIMIT_MAX = 100
today = date.today()

lines, flags = [], []


def check_ollama():
    try:
        with urllib.request.urlopen(OLLAMA_URL, timeout=5) as r:
            data = json.load(r)
        models = [m["name"] for m in data.get("models", [])]
        if "qwen2.5-coder:7b" in models:
            lines.append("Ollama up, qwen2.5-coder:7b present")
        else:
            flags.append(
                f"Ollama up but qwen2.5-coder:7b MISSING (have: {models}) "
                f"-> local routing will fall back to cloud"
            )
    except Exception as e:  # noqa: BLE001
        flags.append(
            f"Ollama UNREACHABLE on :11434 -> local routing falls back to cloud: {e}"
        )


def check_router_default():
    router = os.path.join(REPO, ".github/scripts/llm_router.py")
    if not os.path.exists(router):
        flags.append("llm_router.py not found")
        return
    # Match the ACTUAL default assignment string literal (the 2nd arg of getenv),
    # not the env-var name or docstring mentions. Prevents false alarms.
    txt = open(router).read()
    m = re.search(r'os\.getenv\([^,]*,\s*"([^"]+)"', txt)
    default = m.group(1) if m else ""
    if "1234" in default:
        flags.append(
            "llm_router.py defaults to dead LM Studio :1234 -> local routing broken"
        )
    elif "11434" in default:
        lines.append("llm_router.py defaults to Ollama :11434")
    else:
        flags.append(f"llm_router.py local_url default unexpected: '{default}'")


def check_drift_harness():
    try:
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/agent_drift_eval.py",
                "-q",
                "--no-cov",
                "-p",
                "no:cacheprovider",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode == 0:
            lines.append("Agent drift eval harness: PASS (0 guardrail drift)")
        else:
            flags.append(
                "Agent drift eval harness FAILED -> guardrail behavior changed! "
                "Run: pytest tests/agent_drift_eval.py"
            )
    except Exception as e:  # noqa: BLE001
        flags.append(f"Could not run drift harness: {e}")


def check_clocks():
    pat_days = (PAT_EXPIRY - today).days
    if pat_days <= 30:
        flags.append(f"PAT expires in {pat_days} days (by {PAT_EXPIRY}) -> ROTATE NOW")
    elif pat_days <= 90:
        flags.append(
            f"PAT expires in {pat_days} days ({PAT_EXPIRY}) -> schedule rotation"
        )
    else:
        lines.append(f"PAT valid {pat_days} days ({PAT_EXPIRY})")

    drc_days = (today - DRC_LAST).days
    if drc_days >= 90:
        flags.append(
            f"DRC x-gadgetlab-token age {drc_days} days (rotated {DRC_LAST}) "
            f"-> consider rotation (manual, n8n)"
        )
    else:
        lines.append(f"DRC token age {drc_days} days (rotated {DRC_LAST})")


def check_scale_guardrails():
    """Vision II backstop: scale ceilings must not be lifted silently."""
    cfg = os.path.join(REPO, "core", "agent_config.py")
    if os.path.exists(cfg):
        t = open(cfg).read()
        m = re.search(r"llm_max_cost_usd:\s*float\s*=\s*([0-9.]+)", t)
        cap = float(m.group(1)) if m else None
        if cap is not None and cap <= COST_CAP_MAX:
            lines.append(f"LLM cost cap intact (${cap:g}/run)")
        else:
            flags.append(
                f"LLM cost cap DRIFTED to ${cap}/run (> {COST_CAP_MAX:g}) "
                f"-> scale guardrail lifted, budget risk"
            )
    pol = os.path.join(REPO, "config", "policies.yaml")
    if os.path.exists(pol):
        t = open(pol).read()
        m = re.search(r"max_operations_per_hour:\s*(\d+)", t)
        lim = int(m.group(1)) if m else None
        if lim is not None and lim <= OP_LIMIT_MAX:
            lines.append(f"Rate limit intact ({lim} ops/hr)")
        else:
            flags.append(
                f"Rate limit DRIFTED to {lim} ops/hr (> {OP_LIMIT_MAX}) "
                f"-> scale guardrail lifted"
            )


def check_autonomy_kill_switch():
    """THE most important guardrail: the agent must NEVER silently go live.

    Safe state = dry_run True AND require_approval True AND auto_merge False.
    Three silent-bypass paths exist and all are checked:
      1. Code defaults in core/agent_config.py (dry_run/require_approval/auto_merge)
      2. Env overrides: AGENT_DRY_RUN=false, AGENT_REQUIRE_APPROVAL=false,
         AGENT_AUTO_MERGE=true  (any flag: AGENT_<FLAG>=true|false)
      3. autopilot/staleness_engine.py: ENABLE_LIVE_MODE=true -> dry_run=LIVE
    """
    cfg = os.path.join(REPO, "core", "agent_config.py")
    live = []  # reasons the agent could be live
    if os.path.exists(cfg):
        t = open(cfg).read()
        m = re.search(r"dry_run:\s*bool\s*=\s*(\w+)", t)
        if m and m.group(1) != "True":
            live.append(f"dry_run code default is {m.group(1)} (must be True)")
        m = re.search(r"require_approval:\s*bool\s*=\s*(\w+)", t)
        if m and m.group(1) != "True":
            live.append(f"require_approval code default is {m.group(1)} (must be True)")
        m = re.search(r"auto_merge:\s*bool\s*=\s*(\w+)", t)
        if m and m.group(1) != "False":
            live.append(f"auto_merge code default is {m.group(1)} (must be False)")

    # Env overrides (the silent path most likely to bite)
    for var in ("AGENT_DRY_RUN", "AGENT_REQUIRE_APPROVAL"):
        if os.environ.get(var, "").lower() == "false":
            live.append(f"env {var}=false -> kills the approval gate")
    if os.environ.get("AGENT_AUTO_MERGE", "").lower() == "true":
        live.append("env AGENT_AUTO_MERGE=true -> auto-merge enabled")
    if os.environ.get("ENABLE_LIVE_MODE", "").lower() == "true":
        live.append(
            "env ENABLE_LIVE_MODE=true -> staleness engine runs LIVE (dry_run off)"
        )

    # Config yaml
    yml = os.path.join(REPO, "config", "agent_config.yaml")
    if os.path.exists(yml):
        t = open(yml).read()
        m = re.search(r"require_approval:\s*(\w+)", t)
        if m and m.group(1).lower() != "true":
            live.append(
                f"config/agent_config.yaml require_approval={m.group(1)} (must be true)"
            )

    if live:
        flags.append(
            "AUTONOMY KILL-SWITCH DISABLED -> agent may perform REAL GitHub "
            f"writes without approval: {'; '.join(live)}"
        )
    else:
        lines.append(
            "Autonomy kill-switch intact (dry_run=True, require_approval=True, "
            "auto_merge=False; no live env overrides)"
        )


check_ollama()
check_router_default()
check_drift_harness()
check_clocks()
check_scale_guardrails()
check_autonomy_kill_switch()

print(f"GadgetLab Agent Maintenance - {today.isoformat()}")
if flags:
    print("ITEMS NEEDING ATTENTION:")
    for f in flags:
        print(f"  ! {f}")
if lines:
    print("Healthy:")
    for l in lines:
        print(f"  . {l}")
if not flags and not lines:
    print("  (no signal)")
