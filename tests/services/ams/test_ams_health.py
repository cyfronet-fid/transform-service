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
    assert stats.consecutive_errors == 1
    assert stats.aggregate_errors == 2

    report = stats.to_dict(alive=True)
    assert report["messages_received"] == 5
    assert report["messages_processed"] == 1
    assert report["consecutive_poll_errors"] == 1
    assert report["consecutive_processing_errors"] == 1
    assert report["consecutive_errors"] == 1
    assert report["aggregate_errors"] == 2
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


@pytest.mark.asyncio
async def test_independent_error_counters_in_health_status():
    tracker = AMSHealthTracker()

    async def dummy():
        await asyncio.sleep(10)

    task = asyncio.create_task(dummy())
    tracker.register_consumer("sub-indep", task=task)

    # 2 poll errors
    tracker.record_poll_error("sub-indep")
    tracker.record_poll_error("sub-indep")
    assert tracker.get_stats("sub-indep").consecutive_poll_errors == 2

    # Poll succeeds -> consecutive_poll_errors resets to 0
    tracker.record_poll_success("sub-indep", count=1)
    assert tracker.get_stats("sub-indep").consecutive_poll_errors == 0

    # 2 processing errors
    tracker.record_processing_error("sub-indep")
    tracker.record_processing_error("sub-indep")
    assert tracker.get_stats("sub-indep").consecutive_processing_errors == 2

    # Verify consecutive_errors reflects max consecutive errors (2), aggregate_errors reflects sum (2)
    stats = tracker.get_stats("sub-indep")
    assert stats.consecutive_errors == 2
    assert stats.aggregate_errors == 2

    # Health status MUST remain healthy because neither counter exceeded threshold (> 3)
    status = tracker.get_health_status(ams_enabled=True)
    assert status["status"] == "healthy"

    # Now add 2 more processing errors -> consecutive_processing_errors becomes 4 (> 3)
    tracker.record_processing_error("sub-indep")
    tracker.record_processing_error("sub-indep")
    assert tracker.get_stats("sub-indep").consecutive_processing_errors == 4

    status_degraded = tracker.get_health_status(ams_enabled=True)
    assert status_degraded["status"] == "degraded"

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_ams_consume_loop_exceeds_max_delivery_attempts_and_dlqs(mocker):
    from app.services.ams.client import ams_consume_loop, retry_tracker
    from app.settings import settings

    retry_tracker.clear()
    encoded_data = base64.b64encode(b'{"key": "corrupt"}').decode("utf-8")
    mock_messages = [
        {
            "ackId": "ack-poison-1",
            "message": {"messageId": "msg-poison-1", "data": encoded_data},
        }
    ]

    mocker.patch.object(settings, "AMS_MAX_DELIVERY_ATTEMPTS", 3)
    mocker.patch.object(settings, "AMS_DLQ_TOPIC", "transformer-dlq")

    mock_publish_dlq = mocker.patch(
        "app.services.ams.client.publish_to_dlq", return_value=True
    )
    mock_ack = mocker.patch("app.services.ams.client.ack_messages", return_value=True)
    mocker.patch("app.services.ams.client.process_message", return_value=False)

    # Attempt 1: fails, not ACKed
    mocker.patch(
        "app.services.ams.client.pull_messages",
        side_effect=[mock_messages, asyncio.CancelledError()],
    )
    with pytest.raises(asyncio.CancelledError):
        await ams_consume_loop("sub-test")

    assert retry_tracker.get_attempts("msg-poison-1") == 1
    mock_ack.assert_not_called()
    mock_publish_dlq.assert_not_called()

    # Attempt 2: fails, not ACKed
    mocker.patch(
        "app.services.ams.client.pull_messages",
        side_effect=[mock_messages, asyncio.CancelledError()],
    )
    with pytest.raises(asyncio.CancelledError):
        await ams_consume_loop("sub-test")

    assert retry_tracker.get_attempts("msg-poison-1") == 2
    mock_ack.assert_not_called()
    mock_publish_dlq.assert_not_called()

    # Attempt 3 (reaches max_attempts=3): routes to DLQ and ACKs!
    mocker.patch(
        "app.services.ams.client.pull_messages",
        side_effect=[mock_messages, asyncio.CancelledError()],
    )
    with pytest.raises(asyncio.CancelledError):
        await ams_consume_loop("sub-test")

    mock_publish_dlq.assert_called_once()
    mock_ack.assert_called_once_with("sub-test", ["ack-poison-1"])
    # After DLQ routing and ACK, tracker entry is reset
    assert retry_tracker.get_attempts("msg-poison-1") == 0


@pytest.mark.asyncio
async def test_run_consumer_task_retries_on_ensure_subscription_failure(mocker):
    from app.services.ams.startup import run_consumer_task

    call_count = 0

    async def mock_ensure_sub(topic, sub):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("AMS connection refused")
        return

    mocker.patch(
        "app.services.ams.startup.ensure_subscription", side_effect=mock_ensure_sub
    )
    mock_consume = mocker.patch(
        "app.services.ams.startup.ams_consume_loop",
        side_effect=asyncio.CancelledError(),
    )

    with pytest.raises(asyncio.CancelledError):
        await run_consumer_task(
            topic="adapter-update",
            subscription_name="transformer-adapter-update",
            initial_backoff=0.01,
            max_backoff=0.05,
            backoff_factor=1.5,
        )

    # ensure_subscription was attempted multiple times and recovered
    assert call_count >= 3
    mock_consume.assert_called_once_with("transformer-adapter-update")
