"""Unit tests for core/message_queue.py (in-memory mode)."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import patch

from core.message_queue import MessageQueue


def run(coro):
    return asyncio.run(coro)


def _make_queue(config=None):
    """Create a MessageQueue in in-memory mode."""
    cfg = config or {}
    with patch("core.message_queue.MessageQueue._init_redis", return_value=False):
        mq = MessageQueue(cfg)
    return mq


class TestMessageQueueInit:
    def test_init_without_redis_creates_in_memory_queue(self):
        mq = _make_queue()
        assert mq._redis_client is None
        assert hasattr(mq, "_in_memory_queue")

    def test_initial_queue_is_empty(self):
        mq = _make_queue()
        assert mq._in_memory_queue == []


class TestPublish:
    def test_publish_adds_to_in_memory_queue(self):
        mq = _make_queue()
        run(mq.publish("test-channel", {"event": "ping"}))
        assert len(mq._in_memory_queue) == 1
        assert mq._in_memory_queue[0]["channel"] == "test-channel"
        assert mq._in_memory_queue[0]["data"] == {"event": "ping"}

    def test_multiple_publishes_accumulate(self):
        mq = _make_queue()
        run(mq.publish("chan", {"n": 1}))
        run(mq.publish("chan", {"n": 2}))
        assert len(mq._in_memory_queue) == 2


class TestSubscribe:
    def test_subscribe_registers_callback(self):
        mq = _make_queue()

        async def callback(msg):
            pass

        run(mq.subscribe("my-channel", callback))
        assert "my-channel" in mq._subscriptions
        assert mq._subscriptions["my-channel"] is callback


class TestUnsubscribe:
    def test_unsubscribe_removes_channel(self):
        mq = _make_queue()

        async def cb(msg):
            pass

        run(mq.subscribe("ch", cb))
        run(mq.unsubscribe("ch"))
        assert "ch" not in mq._subscriptions

    def test_unsubscribe_nonexistent_channel_is_noop(self):
        mq = _make_queue()
        run(mq.unsubscribe("ghost-channel"))  # should not raise


class TestEnqueueDequeue:
    def test_enqueue_and_dequeue_roundtrip(self):
        mq = _make_queue()
        task = {"action": "do_thing", "params": {}}
        run(mq.enqueue("work", task))
        result = run(mq.dequeue("work"))
        assert result == task

    def test_dequeue_empty_queue_returns_none(self):
        mq = _make_queue()
        result = run(mq.dequeue("empty-queue"))
        assert result is None

    def test_high_priority_task_dequeued_first(self):
        mq = _make_queue()
        run(mq.enqueue("prio", {"id": "low"}, priority=0))
        run(mq.enqueue("prio", {"id": "high"}, priority=10))
        # Both go to same in-memory queue; sorted by descending priority
        result = run(mq.dequeue("prio"))
        assert result == {"id": "high"}

    def test_multiple_tasks_dequeued_in_order(self):
        mq = _make_queue()
        run(mq.enqueue("tasks", {"seq": 1}, priority=5))
        run(mq.enqueue("tasks", {"seq": 2}, priority=5))
        first = run(mq.dequeue("tasks"))
        second = run(mq.dequeue("tasks"))
        # Both same priority — order depends on insertion; ensure both are returned
        assert {first["seq"], second["seq"]} == {1, 2}


class TestGetQueueSize:
    def test_queue_size_reflects_enqueued_items(self):
        mq = _make_queue()
        assert run(mq.get_queue_size("q")) == 0
        run(mq.enqueue("q", {"x": 1}))
        run(mq.enqueue("q", {"x": 2}))
        assert run(mq.get_queue_size("q")) == 2

    def test_queue_size_decreases_after_dequeue(self):
        mq = _make_queue()
        run(mq.enqueue("q", {"x": 1}))
        run(mq.dequeue("q"))
        assert run(mq.get_queue_size("q")) == 0


class TestGetMessage:
    def test_get_message_returns_published_message(self):
        mq = _make_queue()
        run(mq.publish("events", {"type": "ready"}))
        msg = run(mq.get_message("events"))
        assert msg == {"type": "ready"}

    def test_get_message_returns_none_for_empty_channel(self):
        mq = _make_queue()
        msg = run(mq.get_message("empty"))
        assert msg is None

    def test_get_message_only_returns_matching_channel(self):
        mq = _make_queue()
        run(mq.publish("chan-a", {"from": "a"}))
        run(mq.publish("chan-b", {"from": "b"}))
        msg = run(mq.get_message("chan-b"))
        assert msg == {"from": "b"}


class TestClose:
    def test_close_does_not_raise_without_redis(self):
        mq = _make_queue()
        mq.close()  # should not raise
