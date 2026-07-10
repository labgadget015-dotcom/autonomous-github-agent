#!/usr/bin/env python3
"""
Prometheus metrics exporter for the Autonomous GitHub Agent pipeline.

Why this exists
---------------
`monitoring/prometheus.yml` already scrapes a job named `agent` at
`agent:8000`, but nothing in the codebase exposes a `/metrics` endpoint, so
the Grafana dashboard has no data. This module fixes that gap WITHOUT adding
any third-party dependency (the prometheus client is not in requirements.txt)
by speaking the Prometheus text-exposition format directly over stdlib
http.server.

What it tracks
--------------
- drc_loop_runs_total          counter  (success / failure) DRC Agent Loop runs
- drc_loop_duration_seconds     summary  wall-clock time of a DRC run
- risk_score                    histogram risk score of evaluated actions (0-10)
- overseer_runs_total           counter  overseer/automation runs (success/failure)
- regression_alerts_total       counter  Slack alerts emitted on regression

Usage (sidecar)
---------------
    python monitoring/metrics_exporter.py --port 8000

Usage (import)
--------------
    from monitoring.metrics_exporter import metrics
    metrics.drc_run(duration_s=12.3, success=True)
    metrics.observe_risk_score(4.2)
    # then `metrics.render()` returns the Prometheus text payload
"""

from __future__ import annotations

import argparse
import math
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Risk-score histogram buckets: 0-2.9 LOW, 3-5.9 MEDIUM, 6-7.9 HIGH, 8-10 CRITICAL
RISK_BUCKETS = (3.0, 6.0, 8.0, 10.0, math.inf)


def _bucket_index(value: float, buckets: tuple[float, ...]) -> int:
    """Return the index of the first bucket whose upper bound >= value."""
    for i, upper in enumerate(buckets):
        if value <= upper:
            return i
    return len(buckets) - 1


class Counter:
    """A monotonically increasing counter with label support."""

    def __init__(self, name: str, description: str, label_keys: tuple[str, ...] = ()):
        self.name = name
        self.description = description
        self.label_keys = label_keys
        self._lock = threading.Lock()
        # series[(labelval, ...)] = count
        self._series: dict[tuple[str, ...], float] = {}

    def inc(self, amount: float = 1.0, labels: tuple[str, ...] = ()) -> None:
        if amount < 0:
            raise ValueError("counter cannot decrease")
        with self._lock:
            self._series[labels] = self._series.get(labels, 0.0) + amount

    def _render(self) -> str:
        out = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} counter"]
        with self._lock:
            if not self._series:
                # emit a zero series so the metric always exists
                out.append(f"{self.name} 0")
            for labels, value in sorted(self._series.items()):
                suffix = self._label_suffix(labels)
                out.append(f"{self.name}{suffix} {value:g}")
        return "\n".join(out) + "\n"

    def _label_suffix(self, labels: tuple[str, ...]) -> str:
        if not labels:
            return ""
        parts = [f'{k}="{v}"' for k, v in zip(self.label_keys, labels, strict=False)]
        return "{" + ",".join(parts) + "}"


class Summary:
    """A summary (count + sum) with label support. Good enough for run duration."""

    def __init__(self, name: str, description: str, label_keys: tuple[str, ...] = ()):
        self.name = name
        self.description = description
        self.label_keys = label_keys
        self._lock = threading.Lock()
        self._series: dict[tuple[str, ...], list[float]] = {}  # [count, sum]

    def observe(self, value: float, labels: tuple[str, ...] = ()) -> None:
        with self._lock:
            cur = self._series.setdefault(labels, [0.0, 0.0])
            cur[0] += 1
            cur[1] += value

    def _render(self) -> str:
        out = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} summary"]
        with self._lock:
            if not self._series:
                out.append(f"{self.name}_count 0")
                out.append(f"{self.name}_sum 0")
            for labels, (count, total) in sorted(self._series.items()):
                suffix = self._label_suffix(labels)
                out.append(f"{self.name}_count{suffix} {count:g}")
                out.append(f"{self.name}_sum{suffix} {total:g}")
        return "\n".join(out) + "\n"

    def _label_suffix(self, labels: tuple[str, ...]) -> str:
        if not labels:
            return ""
        parts = [f'{k}="{v}"' for k, v in zip(self.label_keys, labels, strict=False)]
        return "{" + ",".join(parts) + "}"


class Histogram:
    """A histogram with fixed buckets. Used for risk-score distribution."""

    def __init__(self, name: str, description: str, buckets: tuple[float, ...]):
        self.name = name
        self.description = description
        self.buckets = buckets
        self._lock = threading.Lock()
        # series[(labelval,...)] = [bucket_counts..., +Inf_count, sum]
        self._series: dict[tuple[str, ...], list[float]] = {}

    def observe(self, value: float, labels: tuple[str, ...] = ()) -> None:
        with self._lock:
            buckets = list(self.buckets)
            counts = self._series.setdefault(labels, [0.0] * (len(buckets) + 1))
            idx = _bucket_index(value, tuple(buckets))
            counts[idx] += 1
            counts[-1] += value  # last slot = sum

    def _render(self) -> str:
        out = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} histogram",
        ]
        with self._lock:
            if not self._series:
                out.append(f"{self.name}_count 0")
                out.append(f"{self.name}_sum 0")
            for labels, counts in sorted(self._series.items()):
                suffix = self._label_suffix(labels)
                cumulative = 0.0
                for i, upper in enumerate(self.buckets):
                    cumulative += counts[i]
                    out.append(f'{self.name}_bucket{suffix}le="{upper}" {cumulative:g}')
                cumulative += counts[-1] if len(self.buckets) < len(counts) else 0
                # +Inf bucket
                total_count = sum(counts[:-1])
                out.append(f'{self.name}_bucket{suffix}le="+Inf" {total_count:g}')
                out.append(f"{self.name}_count{suffix} {total_count:g}")
                out.append(f"{self.name}_sum{suffix} {counts[-1]:g}")
        return "\n".join(out) + "\n"

    def _label_suffix(self, labels: tuple[str, ...]) -> str:
        if not labels:
            return ""
        parts = [f'outcome="{v}"' for v in labels]
        return "{" + ",".join(parts) + "}"


class Metrics:
    """Central registry of all pipeline metrics."""

    def __init__(self) -> None:
        self.drc_runs = Counter(
            "drc_loop_runs_total",
            "Total DRC Agent Loop runs by outcome.",
            label_keys=("outcome",),
        )
        self.drc_duration = Summary(
            "drc_loop_duration_seconds",
            "Wall-clock duration of a DRC Agent Loop run.",
            label_keys=("outcome",),
        )
        self.risk_score = Histogram(
            "risk_score",
            "Distribution of action risk scores (0-10) evaluated by the pipeline.",
            RISK_BUCKETS,
        )
        self.overseer_runs = Counter(
            "overseer_runs_total",
            "Total overseer/automation runs by outcome.",
            label_keys=("outcome",),
        )
        self.regression_alerts = Counter(
            "regression_alerts_total",
            "Total Slack regression alerts emitted.",
            label_keys=("reason",),
        )

    # --- convenience API ---------------------------------------------------
    def drc_run(self, duration_s: float, success: bool) -> None:
        outcome = "success" if success else "failure"
        self.drc_runs.inc(labels=(outcome,))
        self.drc_duration.observe(duration_s, labels=(outcome,))

    def observe_risk_score(self, score: float) -> None:
        self.risk_score.observe(float(score))

    def overseer_run(self, success: bool) -> None:
        self.overseer_runs.inc(labels=("success" if success else "failure",))

    def alert(self, reason: str) -> None:
        self.regression_alerts.inc(labels=(reason,))

    def render(self) -> str:
        parts = [
            self.drc_runs._render(),
            self.drc_duration._render(),
            self.risk_score._render(),
            self.overseer_runs._render(),
            self.regression_alerts._render(),
        ]
        return "\n".join(parts)


metrics = Metrics()


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if self.path in ("/metrics", "/"):
            payload = metrics.render().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(
        self, format: str, *args
    ) -> None:  # noqa: A002 — silence default stderr logging
        pass


def serve(port: int = 8000, host: str = "0.0.0.0") -> ThreadingHTTPServer:
    """Start the metrics HTTP server. Returns the server (call .shutdown() to stop)."""
    server = ThreadingHTTPServer((host, port), _Handler)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Autonomous GitHub Agent metrics exporter"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to serve /metrics on"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    args = parser.parse_args()
    srv = serve(args.port, args.host)
    print(
        f"metrics exporter listening on http://{args.host}:{args.port}/metrics",
        flush=True,
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
