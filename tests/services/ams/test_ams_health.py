"""Unit tests for AMS health tracker and health check endpoint"""

import asyncio
import base64
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.server import get_app
from app.services.ams.health import (
    AMSConsumerStats,
    AMSHealthTracker,
    ams_health_tracker,
)


def test_ams_consumer_stats_initialization():
    stats = AMSConsumerStats("sub-test")
    assert stats.subscription == "sub-test"
    assert stats.messages_received == 0
    assert stats.messages_processed == 0
    assert stats.consecutive_poll_errors == 0
    assert stats.consecutive_processing_errors == 0
    assert stats.consecutive_errors == 0
    assert stats.last_successful_poll is None

    report = stats.to_dict(alive=True)
    assert report["alive"] is True
    assert report["last_successful_poll"] is None
    assert report["messages_received"] == 0
    assert report["messages_processed"] == 0
    assert report["consecutive_poll_errors"] == 0
    assert report["consecutive_processing_errors"] == 0
    assert report["consecutive_errors"] == 0


def test_ams_consumer_stats_recording():
    stats = AMSConsumerStats("sub-test")
    stats.record_poll_success(count=5)
    assert stats.messages_received == 5
    assert stats.last_successful_poll is not None
    assert stats.consecutive_poll_errors == 0
    assert stats.consecutive_errors == 0

    stats.record_message_processed()
    assert stats.messages_processed == 1
    assert stats.consecutive_processing_errors == 0
    assert stats.consecutive_errors == 0

    stats.record_poll_error()
    assert stats.consecutive_poll_errors == 1
    assert stats.consecutive_errors == 1

    stats.record_processing_error()
    assert stats.consecutive_processing_errors == 1
    assert stats.consecutive_errors == 2

    report = stats.to_dict(alive=True)
    assert report["messages_received"] == 5
    assert report["messages_processed"] == 1
    assert report["consecutive_poll_errors"] == 1
    assert report["consecutive_processing_errors"] == 1
    assert report["consecutive_errors"] == 2
    assert report["last_successful_poll"].endswith("Z")


@pytest.mark.asyncio
async def test_ams_health_tracker_overall_status():
    tracker = AMSHealthTracker()
    tracker.record_poll_success("sub-1", count=2)
    tracker.record_message_processed("sub-1")

    # Create dummy running task
    async def dummy_loop():
        await asyncio.sleep(10)

    task = asyncio.create_task(dummy_loop())
    tracker.set_task("sub-1", task)

    status = tracker.get_health_status(ams_enabled=True)
    assert status["status"] == "healthy"
    assert "sub-1" in status["consumers"]
    c1 = status["consumers"]["sub-1"]
    assert c1["alive"] is True
    assert c1["messages_received"] == 2
    assert c1["messages_processed"] == 1
    assert c1["consecutive_errors"] == 0

    # Cancel task to test unhealthy status
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    status_cancelled = tracker.get_health_status(ams_enabled=True)
    assert status_cancelled["status"] == "unhealthy"
    assert status_cancelled["consumers"]["sub-1"]["alive"] is False


def test_ams_health_endpoint():
    app = get_app()
    client = TestClient(app)

    response = client.get("/ams/health")
    assert response.status_code == 200
    json_data = response.json()
    assert "status" in json_data
    assert "consumers" in json_data


@pytest.mark.asyncio
async def test_ams_health_tracker_startup_and_poll_threshold():
    tracker = AMSHealthTracker()

    # Immediately after startup: task is running, but last_successful_poll is None -> degraded
    async def dummy_loop():
        await asyncio.sleep(10)

    task = asyncio.create_task(dummy_loop())
    tracker.register_consumer("sub-1", task=task)

    status_startup = tracker.get_health_status(ams_enabled=True)
    assert status_startup["status"] == "unhealthy"
    assert status_startup["consumers"]["sub-1"]["alive"] is True
    assert status_startup["consumers"]["sub-1"]["last_successful_poll"] is None

    # After first successful poll -> becomes healthy
    tracker.record_poll_success("sub-1", count=1)
    status_polled = tracker.get_health_status(ams_enabled=True)
    assert status_polled["status"] == "healthy"

    # If poll becomes stale (> threshold) -> becomes degraded
    stats = tracker.get_stats("sub-1")
    stats.last_successful_poll = datetime.now(timezone.utc) - timedelta(seconds=200)
    status_stale = tracker.get_health_status(
        ams_enabled=True, poll_threshold_seconds=120
    )
    assert status_stale["status"] == "unhealthy"

    # If error threshold exceeded -> degraded
    stats.last_successful_poll = datetime.now(timezone.utc)
    for _ in range(4):
        tracker.record_processing_error("sub-1")
    status_errors = tracker.get_health_status(ams_enabled=True)
    assert status_errors["status"] == "degraded"

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_ams_consume_loop_ack_when_process_message_succeeds(mocker):
    from app.services.ams.client import ams_consume_loop

    encoded_data = base64.b64encode(b'{"key": "value"}').decode("utf-8")
    mock_messages = [{"ackId": "ack-123", "message": {"data": encoded_data}}]

    tracker = ams_health_tracker
    tracker.clear()
    tracker.register_consumer("sub-test")

    mocker.patch(
        "app.services.ams.client.pull_messages",
        side_effect=[mock_messages, asyncio.CancelledError()],
    )
    mock_process = mocker.patch(
        "app.services.ams.client.process_message", return_value=True
    )
    mock_ack = mocker.patch("app.services.ams.client.ack_messages", return_value=True)

    with pytest.raises(asyncio.CancelledError):
        await ams_consume_loop("sub-test")

    mock_process.assert_called_once()
    mock_ack.assert_called_once_with("sub-test", ["ack-123"])
    assert tracker.get_stats("sub-test").messages_processed == 1
    assert tracker.get_stats("sub-test").consecutive_processing_errors == 0


@pytest.mark.asyncio
async def test_ams_consume_loop_no_ack_when_process_message_fails(mocker):
    from app.services.ams.client import ams_consume_loop

    encoded_data = base64.b64encode(b'{"key": "value"}').decode("utf-8")
    mock_messages = [{"ackId": "ack-fail", "message": {"data": encoded_data}}]

    tracker = ams_health_tracker
    tracker.clear()
    tracker.register_consumer("sub-test")

    mocker.patch(
        "app.services.ams.client.pull_messages",
        side_effect=[mock_messages, asyncio.CancelledError()],
    )
    mocker.patch("app.services.ams.client.process_message", return_value=False)
    mock_ack = mocker.patch("app.services.ams.client.ack_messages")

    with pytest.raises(asyncio.CancelledError):
        await ams_consume_loop("sub-test")

    mock_ack.assert_not_called()
    assert tracker.get_stats("sub-test").messages_processed == 0
    assert tracker.get_stats("sub-test").consecutive_processing_errors == 1


@pytest.mark.asyncio
async def test_ams_consume_loop_no_ack_when_process_message_raises(mocker):
    from app.services.ams.client import ams_consume_loop

    encoded_data = base64.b64encode(b'{"key": "value"}').decode("utf-8")
    mock_messages = [{"ackId": "ack-err", "message": {"data": encoded_data}}]

    tracker = ams_health_tracker
    tracker.clear()
    tracker.register_consumer("sub-test")

    mocker.patch(
        "app.services.ams.client.pull_messages",
        side_effect=[mock_messages, asyncio.CancelledError()],
    )
    mocker.patch(
        "app.services.ams.client.process_message",
        side_effect=RuntimeError("Solr connection error"),
    )
    mock_ack = mocker.patch("app.services.ams.client.ack_messages")

    with pytest.raises(asyncio.CancelledError):
        await ams_consume_loop("sub-test")

    mock_ack.assert_not_called()
    assert tracker.get_stats("sub-test").messages_processed == 0
    assert tracker.get_stats("sub-test").consecutive_processing_errors == 1


@pytest.mark.asyncio
async def test_stop_ams_subscription():
    from app.services.ams.startup import background_tasks, stop_ams_subscription

    background_tasks.clear()

    async def dummy():
        await asyncio.sleep(100)

    t1 = asyncio.create_task(dummy())
    t2 = asyncio.create_task(dummy())
    background_tasks.add(t1)
    background_tasks.add(t2)

    await stop_ams_subscription()

    assert t1.cancelled() or t1.done()
    assert t2.cancelled() or t2.done()
    assert len(background_tasks) == 0
