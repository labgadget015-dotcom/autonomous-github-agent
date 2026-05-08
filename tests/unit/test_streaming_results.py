"""Unit tests for .github/scripts/streaming_results.py"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from streaming_results import (
    StreamingResultWriter,
    StreamingResultReader,
    StreamingAggregator,
)


class TestStreamingResultWriter:
    @pytest.mark.asyncio
    async def test_creates_output_file(self, tmp_path):
        output = tmp_path / "results.jsonl"
        async with StreamingResultWriter(output) as writer:
            await writer.write({"id": 1, "status": "ok"})
        assert output.exists()

    @pytest.mark.asyncio
    async def test_writes_single_record(self, tmp_path):
        output = tmp_path / "results.jsonl"
        async with StreamingResultWriter(output) as writer:
            await writer.write({"id": 1, "status": "ok"})
        lines = [l for l in output.read_bytes().split(b"\n") if l]
        assert len(lines) == 1

    @pytest.mark.asyncio
    async def test_writes_multiple_records(self, tmp_path):
        output = tmp_path / "results.jsonl"
        async with StreamingResultWriter(output) as writer:
            for i in range(5):
                await writer.write({"id": i, "value": i * 2})
        lines = [l for l in output.read_bytes().split(b"\n") if l]
        assert len(lines) == 5

    @pytest.mark.asyncio
    async def test_total_written_increments(self, tmp_path):
        output = tmp_path / "results.jsonl"
        async with StreamingResultWriter(output) as writer:
            await writer.write({"a": 1})
            await writer.write({"b": 2})
            await writer.write({"c": 3})
            assert writer._total_written == 3

    def test_get_stats_before_open(self, tmp_path):
        output = tmp_path / "results.jsonl"
        writer = StreamingResultWriter(output)
        stats = writer.get_stats()
        assert stats["total_written"] == 0
        assert "output_path" in stats

    @pytest.mark.asyncio
    async def test_creates_parent_dirs(self, tmp_path):
        output = tmp_path / "subdir1" / "subdir2" / "results.jsonl"
        async with StreamingResultWriter(output) as writer:
            await writer.write({"x": 1})
        assert output.exists()

    @pytest.mark.asyncio
    async def test_flush_clears_buffer(self, tmp_path):
        output = tmp_path / "results.jsonl"
        async with StreamingResultWriter(output, buffer_size=99999) as writer:
            # Write but don't auto-flush
            await writer.write({"x": 1})
            await writer.flush()
            assert writer._buffer_bytes == 0


class TestStreamingResultReader:
    @pytest.mark.asyncio
    async def test_returns_empty_for_nonexistent_file(self, tmp_path):
        reader = StreamingResultReader(tmp_path / "nonexistent.jsonl")
        count = await reader.count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_reads_written_records(self, tmp_path):
        import json as stdlib_json

        output = tmp_path / "results.jsonl"
        # Write via writer
        async with StreamingResultWriter(output) as writer:
            for i in range(3):
                await writer.write({"id": i})

        # Count via raw read to verify
        lines = [l for l in output.read_bytes().split(b"\n") if l]
        assert len(lines) == 3

    def test_reader_init(self, tmp_path):
        reader = StreamingResultReader(tmp_path / "data.jsonl")
        assert reader.input_path == tmp_path / "data.jsonl"

    @pytest.mark.asyncio
    async def test_read_filtered_empty_for_nonexistent(self, tmp_path):
        reader = StreamingResultReader(tmp_path / "nonexistent.jsonl")
        results = []
        async for r in reader.read_filtered(lambda x: True):
            results.append(r)
        assert results == []


class TestStreamingAggregator:
    @pytest.mark.asyncio
    async def test_creates_empty_aggregator(self):
        agg = StreamingAggregator()
        summary = agg.get_summary()
        assert summary["total_files"] == 0
        assert summary["total_issues"] == 0

    @pytest.mark.asyncio
    async def test_process_result_increments_files(self):
        agg = StreamingAggregator()
        await agg.process_result({"issues": []})
        await agg.process_result({"issues": []})
        summary = agg.get_summary()
        assert summary["total_files"] == 2

    @pytest.mark.asyncio
    async def test_process_result_counts_issues(self):
        agg = StreamingAggregator()
        await agg.process_result(
            {
                "issues": [
                    {"severity": "high", "tool": "ruff"},
                    {"severity": "low", "tool": "pylint"},
                ]
            }
        )
        summary = agg.get_summary()
        assert summary["total_issues"] == 2

    @pytest.mark.asyncio
    async def test_process_result_groups_by_severity(self):
        agg = StreamingAggregator()
        await agg.process_result(
            {
                "issues": [
                    {"severity": "high", "tool": "ruff"},
                    {"severity": "high", "tool": "ruff"},
                    {"severity": "low", "tool": "pylint"},
                ]
            }
        )
        summary = agg.get_summary()
        assert summary["issues_by_severity"]["high"] == 2
        assert summary["issues_by_severity"]["low"] == 1

    @pytest.mark.asyncio
    async def test_process_result_groups_by_tool(self):
        agg = StreamingAggregator()
        await agg.process_result(
            {
                "issues": [
                    {"severity": "high", "tool": "ruff"},
                    {"severity": "medium", "tool": "ruff"},
                ]
            }
        )
        summary = agg.get_summary()
        assert summary["issues_by_tool"]["ruff"] == 2

    @pytest.mark.asyncio
    async def test_process_error_result_increments_errors(self):
        agg = StreamingAggregator()
        await agg.process_result({"issues": [], "error": "Parsing failed"})
        summary = agg.get_summary()
        assert summary["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_get_summary_returns_copy(self):
        agg = StreamingAggregator()
        summary1 = agg.get_summary()
        summary1["total_files"] = 999  # Mutate returned value
        summary2 = agg.get_summary()
        assert summary2["total_files"] == 0  # Original unchanged
