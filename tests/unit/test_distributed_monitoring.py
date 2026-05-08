"""Unit tests for .github/scripts/distributed_monitoring.py"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from distributed_monitoring import Alert, HealthChecker, PerformanceMonitor


class TestAlertDataclass:
    def _make_alert(self, severity="warning"):
        return Alert(
            severity=severity,
            metric="cpu_usage",
            threshold=80.0,
            current_value=85.0,
            message="CPU is high",
            timestamp=datetime.now(),
        )

    def test_creates_alert(self):
        alert = self._make_alert()
        assert alert.severity == "warning"
        assert alert.metric == "cpu_usage"

    def test_str_warning_contains_warning(self):
        alert = self._make_alert("warning")
        s = str(alert)
        assert "WARNING" in s

    def test_str_critical_contains_critical(self):
        alert = self._make_alert("critical")
        s = str(alert)
        assert "CRITICAL" in s

    def test_str_info_contains_info(self):
        alert = self._make_alert("info")
        s = str(alert)
        assert "INFO" in s

    def test_str_contains_message(self):
        alert = self._make_alert()
        s = str(alert)
        assert "CPU is high" in s


class TestPerformanceMonitorInit:
    def test_creates_with_default_name(self):
        monitor = PerformanceMonitor()
        assert monitor.service_name == "autonomous-github-agent"

    def test_creates_with_custom_name(self):
        monitor = PerformanceMonitor("my-service")
        assert monitor.service_name == "my-service"

    def test_initial_alerts_empty(self):
        monitor = PerformanceMonitor()
        assert monitor.alerts == []


class TestCheckThreshold:
    def test_critical_threshold_creates_alert(self):
        monitor = PerformanceMonitor()
        monitor.check_threshold("cpu", 95.0, warning=80.0, critical=90.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].severity == "critical"

    def test_warning_threshold_creates_alert(self):
        monitor = PerformanceMonitor()
        monitor.check_threshold("cpu", 85.0, warning=80.0, critical=90.0)
        assert len(monitor.alerts) == 1
        assert monitor.alerts[0].severity == "warning"

    def test_below_warning_creates_no_alert(self):
        monitor = PerformanceMonitor()
        monitor.check_threshold("cpu", 50.0, warning=80.0, critical=90.0)
        assert len(monitor.alerts) == 0

    def test_alert_contains_metric_name(self):
        monitor = PerformanceMonitor()
        monitor.check_threshold("memory_usage", 95.0, warning=80.0, critical=90.0)
        assert monitor.alerts[0].metric == "memory_usage"

    def test_alert_contains_current_value(self):
        monitor = PerformanceMonitor()
        monitor.check_threshold("cpu", 95.0, warning=80.0, critical=90.0)
        assert monitor.alerts[0].current_value == 95.0


class TestGetAlerts:
    def _monitor_with_alerts(self):
        monitor = PerformanceMonitor()
        monitor.check_threshold("cpu", 95.0, warning=80.0, critical=90.0)
        monitor.check_threshold("memory", 85.0, warning=80.0, critical=95.0)
        return monitor

    def test_get_all_alerts(self):
        monitor = self._monitor_with_alerts()
        alerts = monitor.get_alerts()
        assert len(alerts) == 2

    def test_filter_by_critical(self):
        monitor = self._monitor_with_alerts()
        critical = monitor.get_alerts("critical")
        assert all(a.severity == "critical" for a in critical)

    def test_filter_by_warning(self):
        monitor = self._monitor_with_alerts()
        warnings = monitor.get_alerts("warning")
        assert all(a.severity == "warning" for a in warnings)

    def test_filter_returns_empty_for_nonexistent_severity(self):
        monitor = self._monitor_with_alerts()
        result = monitor.get_alerts("info")
        assert result == []


class TestHealthChecker:
    def test_creates_with_empty_checks(self):
        hc = HealthChecker()
        assert hc.checks == {}

    @pytest.mark.asyncio
    async def test_check_disk_space_returns_bool(self):
        hc = HealthChecker()
        result = await hc.check_disk_space()
        assert isinstance(result, bool)
        assert result is True  # Disk should have >10% free in test environment

    @pytest.mark.asyncio
    async def test_check_memory_returns_bool(self):
        hc = HealthChecker()
        result = await hc.check_memory()
        assert isinstance(result, bool)


class TestTraceOperation:
    @pytest.mark.asyncio
    async def test_trace_operation_without_otel(self):
        monitor = PerformanceMonitor()
        monitor.tracer = None  # Force fallback mode
        executed = []
        async with monitor.trace_operation("test_op") as span:
            executed.append(True)
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_trace_operation_times_execution(self, capsys):
        monitor = PerformanceMonitor()
        monitor.tracer = None
        async with monitor.trace_operation("my_operation"):
            pass
        out = capsys.readouterr().out
        assert "my_operation" in out
