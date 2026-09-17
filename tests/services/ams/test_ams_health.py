"""Unit tests for AMS health tracker and health check endpoint"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.server import get_app
from app.services.ams.health import AMSConsumerStats, AMSHealthTracker


def test_ams_consumer_stats_initialization():
    stats = AMSConsumerStats("sub-test")
    assert stats.subscription == "sub-test"
    assert stats.messages_received == 0
    assert stats.messages_processed == 0
    assert stats.consecutive_errors == 0
    assert stats.last_successful_poll is None

    report = stats.to_dict(alive=True)
    assert report["alive"] is True
    assert report["last_successful_poll"] is None
    assert report["messages_received"] == 0
    assert report["messages_processed"] == 0
    assert report["consecutive_errors"] == 0


def test_ams_consumer_stats_recording():
    stats = AMSConsumerStats("sub-test")
    stats.record_poll_success(count=5)
    assert stats.messages_received == 5
    assert stats.last_successful_poll is not None
    assert stats.consecutive_errors == 0

    stats.record_message_processed()
    assert stats.messages_processed == 1
    assert stats.consecutive_errors == 0

    stats.record_error()
    assert stats.consecutive_errors == 1

    report = stats.to_dict(alive=True)
    assert report["messages_received"] == 5
    assert report["messages_processed"] == 1
    assert report["consecutive_errors"] == 1
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
