#!/usr/bin/env bash
# Driver for autonomous-github-agent. Run from anywhere:
#   .claude/skills/run-autonomous-github-agent/driver.sh <cmd> [args]
#
# cmds:
#   setup                      create venv (outside the repo) + install deps
#   cli <args...>              python -m autonomous_agent.cli <args>   (clean cwd)
#   risk '<json>'              core.risk_scorer.score_pull_request(**json) -> markdown
#   mcp list                   list tools of mcp_server/server.py over real MCP stdio
#   mcp call <tool> '<json>'   call one MCP tool (DRY_RUN=true unless exported)
#   script <file> [args...]    run .github/scripts/<file> with the venv python
#   overseer [args...]         run_overseer.py (default --output goes to $AGA_WORK)
#   autopilot [args...]        autopilot/autopilot.py daily summary (read-only GitHub)
#   test [pytest args...]      full suite from a clean cwd (no .env pollution)
#
# Env: AGA_VENV (default ~/.venvs/autonomous-github-agent)
#      AGA_WORK (default ${TMPDIR:-/tmp}/aga-work) - clean cwd; audit.db + outputs land here
#      GITHUB_TOKEN (default: `gh auth token`)
set -euo pipefail

SKILL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SKILL_DIR/../../.." && pwd)
VENV=${AGA_VENV:-$HOME/.venvs/autonomous-github-agent}
PY=$VENV/bin/python
WORK=${AGA_WORK:-${TMPDIR:-/tmp}/aga-work}
mkdir -p "$WORK"

need_venv() { [ -x "$PY" ] || { echo "no venv at $VENV - run: $0 setup" >&2; exit 2; }; }
gh_env() {
  if [ -z "${GITHUB_TOKEN:-}" ]; then
    GITHUB_TOKEN=$(gh auth token 2>/dev/null || true)
  fi
  [ -n "${GITHUB_TOKEN:-}" ] || echo "warn: GITHUB_TOKEN unset (gh not logged in?)" >&2
  export GITHUB_TOKEN
  # LLMClient() builds an OpenAI client eagerly even for commands that never call it.
  export LLM_API_KEY=${LLM_API_KEY:-dummy-not-used}
  export PYTHONPATH=$REPO${PYTHONPATH:+:$PYTHONPATH}
}

cmd=${1:-help}; shift || true
case "$cmd" in
  setup)
    command -v uv >/dev/null || { echo "need uv: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2; exit 2; }
    [ -x "$PY" ] || uv venv --python 3.11 "$VENV"
    uv pip install --python "$PY" -r "$REPO/requirements.txt" \
      pytest pytest-cov pytest-xdist pytest-asyncio 'mcp<2'
    ;;
  cli)
    need_venv; gh_env; cd "$WORK"
    exec "$PY" -m autonomous_agent.cli "$@"
    ;;
  risk)
    need_venv; cd "$WORK"
    PYTHONPATH=$REPO exec "$PY" -c '
import json, sys
from core.risk_scorer import score_pull_request
r = score_pull_request(**json.loads(sys.argv[1]))
print(r.as_markdown())
print(f"band={r.band.value} score={r.total_score} blocks_auto_merge={r.blocks_auto_merge}")
' "${1:-"{}"}"
    ;;
  mcp)
    need_venv; gh_env; cd "$WORK"
    exec "$PY" "$SKILL_DIR/mcp_client.py" "$@"
    ;;
  script)
    need_venv; gh_env; f=$1; shift
    exec "$PY" "$REPO/.github/scripts/$f" "$@"
    ;;
  overseer)
    need_venv; cd "$REPO"
    case " $* " in *" --output "*) ;; *) set -- "$@" --output "$WORK/overseer-results.json";; esac
    exec "$PY" run_overseer.py "$@"
    ;;
  autopilot)
    need_venv; gh_env; cd "$WORK"
    case " $* " in *" --config "*) ;; *) set -- --config "$REPO/autopilot/config.yaml" "$@";; esac
    case " $* " in *" --output "*) ;; *) set -- "$@" --output "$WORK/DAILY_SUMMARY.md";; esac
    exec "$PY" "$REPO/autopilot/autopilot.py" "$@"
    ;;
  test)
    need_venv; cd "$WORK"
    unset GITHUB_TOKEN
    # cwd is $AGA_WORK, so rewrite repo-relative test paths; default to all of tests/.
    args=(); has_path=0
    for a in "$@"; do
      case "$a" in tests|tests/*) args+=("$REPO/$a"); has_path=1;; *) args+=("$a");; esac
    done
    [ $has_path = 1 ] || args+=("$REPO/tests")
    exec "$PY" -m pytest -c "$REPO/pytest.ini" --rootdir="$REPO" -p no:cacheprovider "${args[@]}"
    ;;
  *)
    sed -n '2,20p' "$0"; [ "$cmd" = help ] || exit 2
    ;;
esac
