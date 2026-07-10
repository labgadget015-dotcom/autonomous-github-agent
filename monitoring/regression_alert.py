#!/usr/bin/env python3
"""
Regression alerting for the Autonomous GitHub Agent pipeline.

Purpose
-------
Catches silent pipeline degradation and posts a notification to Slack
(channel #drc-recommendations) via the same SLACK_WEBHOOK_URL secret the
rest of the repo uses (see .github/scripts/notification_manager.py and
.github/workflows/n8n-health-check.yml).

It is intentionally dependency-light: it uses urllib from the standard
library, with an optional requests fallback so it behaves exactly like the
existing notification_manager.py code path.

Detectable regressions
-----------------------
- coverage dropped below a floor (e.g. 70%)
- DRC loop failure rate over a window exceeds a threshold
- median risk score of evaluated actions climbs above a ceiling

Usage
-----
    from monitoring.regression_alert import RegressionMonitor, metrics
    monitor = RegressionMonitor(metrics, coverage_floor=70.0)
    monitor.check(coverage_pct=current_coverage)
    # or as a CLI:
    python monitoring/regression_alert.py --coverage 68.5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running this script directly (python monitoring/regression_alert.py)
# by making the repo root importable as a package root.
_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import requests  # type: ignore
    _REQUESTS = True
    _urllib = None
except ImportError:  # pragma: no cover
    import urllib.request as _urllib

    _REQUESTS = False
    requests = None  # type: ignore[assignment]

from monitoring.metrics_exporter import metrics  # noqa: E402

DEFAULT_SLACK_CHANNEL = "#drc-recommendations"



class RegressionMonitor:
    """Evaluates pipeline health signals and emits Slack alerts on regression."""

    def __init__(
        self,
        coverage_floor: float = 70.0,
        risk_ceiling: float = 6.0,
        failure_rate_ceiling: float = 0.2,
        slack_webhook: str | None = None,
        channel: str = DEFAULT_SLACK_CHANNEL,
    ) -> None:
        self.coverage_floor = coverage_floor
        self.risk_ceiling = risk_ceiling
        self.failure_rate_ceiling = failure_rate_ceiling
        self.slack_webhook = slack_webhook or os.getenv("SLACK_WEBHOOK_URL")
        self.channel = channel

    # --- signal checks -----------------------------------------------------
    def check_coverage(self, coverage_pct: float) -> str | None:
        """Return an alert reason if coverage is below the floor, else None."""
        if coverage_pct < self.coverage_floor:
            reason = (
                f"coverage regression: {coverage_pct:.2f}% "
                f"below floor {self.coverage_floor:.2f}%"
            )
            self._emit(reason)
            return reason
        return None

    def check_failure_rate(self, successes: int, failures: int) -> str | None:
        """Return an alert reason if the DRC failure rate exceeds the ceiling."""
        total = successes + failures
        if total == 0:
            return None
        rate = failures / total
        if rate > self.failure_rate_ceiling:
            reason = (
                f"DRC failure rate {rate:.1%} "
                f"({failures}/{total}) exceeds ceiling "
                f"{self.failure_rate_ceiling:.1%}"
            )
            self._emit(reason)
            return reason
        return None

    def check_risk_ceiling(self, median_risk: float) -> str | None:
        """Return an alert reason if the median evaluated risk climbs too high."""
        if median_risk > self.risk_ceiling:
            reason = (
                f"median risk score {median_risk:.1f} "
                f"above ceiling {self.risk_ceiling:.1f}"
            )
            self._emit(reason)
            return reason
        return None

    # --- delivery ----------------------------------------------------------
    def _emit(self, reason: str) -> None:
        metrics.alert(reason=reason.split(":")[0])
        self._post_to_slack(reason)

    def _post_to_slack(self, reason: str) -> bool:
        if not self.slack_webhook:
            print(f"[regression-alert] (no SLACK_WEBHOOK_URL) {reason}", file=__import__("sys").stderr)
            return False
        text = (
            f":rotating_light: Pipeline regression detected\n"
            f"*Reason:* {reason}\n"
            f"*Action:* investigate the DRC loop / overseer before the next run."
        )
        payload = {"channel": self.channel, "text": text}
        try:
            if _REQUESTS and requests is not None:
                resp = requests.post(self.slack_webhook, json=payload, timeout=10)
                ok = resp.status_code == 200
            elif _urllib is not None:  # pragma: no cover
                req = _urllib.Request(
                    self.slack_webhook,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with _urllib.urlopen(req, timeout=10) as r:
                    ok = r.status == 200
            else:
                print("[regression-alert] no HTTP client available", file=__import__("sys").stderr)
                return False
        except Exception as exc:  # noqa: BLE001 — surface but never crash the caller
            print(f"[regression-alert] slack post failed: {exc}", file=__import__("sys").stderr)
            return False
        if not ok:
            print("[regression-alert] slack returned non-200", file=__import__("sys").stderr)
        return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Check pipeline health and alert on regression")
    parser.add_argument("--coverage", type=float, default=None, help="Current coverage percent")
    parser.add_argument("--coverage-floor", type=float, default=70.0)
    parser.add_argument("--drc-success", type=int, default=None)
    parser.add_argument("--drc-failure", type=int, default=None)
    parser.add_argument("--median-risk", type=float, default=None)
    args = parser.parse_args()

    monitor = RegressionMonitor(coverage_floor=args.coverage_floor)
    fired = False
    if args.coverage is not None:
        fired = monitor.check_coverage(args.coverage) is not None or fired
    if args.drc_success is not None and args.drc_failure is not None:
        fired = monitor.check_failure_rate(args.drc_success, args.drc_failure) is not None or fired
    if args.median_risk is not None:
        fired = monitor.check_risk_ceiling(args.median_risk) is not None or fired

    raise SystemExit(1 if fired else 0)


if __name__ == "__main__":
    main()
