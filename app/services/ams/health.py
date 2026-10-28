"""AMS Health Check Registry and Statistics Tracker"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.settings import settings


class AMSConsumerStats:
    """Tracks metrics for a single AMS subscription consumer."""

    def __init__(self, subscription: str):
        self.subscription = subscription
        self.last_successful_poll: Optional[datetime] = None
        self.messages_received: int = 0
        self.messages_processed: int = 0
        self.consecutive_poll_errors: int = 0
        self.consecutive_processing_errors: int = 0

    @property
    def consecutive_errors(self) -> int:
        return self.consecutive_poll_errors + self.consecutive_processing_errors

    @consecutive_errors.setter
    def consecutive_errors(self, value: int) -> None:
        self.consecutive_poll_errors = value
        self.consecutive_processing_errors = 0

    def record_poll_success(self, count: int = 0) -> None:
        self.last_successful_poll = datetime.now(timezone.utc)
        self.messages_received += count
        self.consecutive_poll_errors = 0

    def record_poll_error(self) -> None:
        self.consecutive_poll_errors += 1

    def record_message_processed(self) -> None:
        self.messages_processed += 1
        self.consecutive_processing_errors = 0

    def record_processing_error(self) -> None:
        self.consecutive_processing_errors += 1

    def record_error(self) -> None:
        self.record_poll_error()

    def to_dict(self, alive: bool) -> Dict[str, Any]:
        poll_str = None
        if self.last_successful_poll:
            poll_str = self.last_successful_poll.strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "alive": alive,
            "last_successful_poll": poll_str,
            "messages_received": self.messages_received,
            "messages_processed": self.messages_processed,
            "consecutive_poll_errors": self.consecutive_poll_errors,
            "consecutive_processing_errors": self.consecutive_processing_errors,
            "consecutive_errors": self.consecutive_errors,
        }


class AMSHealthTracker:
    """Singleton tracker for all AMS consumers and tasks."""

    def __init__(self):
        self._consumers: Dict[str, AMSConsumerStats] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    def register_consumer(
        self, subscription: str, task: Optional[asyncio.Task] = None
    ) -> AMSConsumerStats:
        if subscription not in self._consumers:
            self._consumers[subscription] = AMSConsumerStats(subscription)
        if task is not None:
            self._tasks[subscription] = task
        return self._consumers[subscription]

    def set_task(self, subscription: str, task: asyncio.Task) -> None:
        self._tasks[subscription] = task

    def get_stats(self, subscription: str) -> AMSConsumerStats:
        if subscription not in self._consumers:
            self._consumers[subscription] = AMSConsumerStats(subscription)
        return self._consumers[subscription]

    def record_poll_success(self, subscription: str, count: int = 0) -> None:
        self.get_stats(subscription).record_poll_success(count)

    def record_poll_error(self, subscription: str) -> None:
        self.get_stats(subscription).record_poll_error()

    def record_message_processed(self, subscription: str) -> None:
        self.get_stats(subscription).record_message_processed()

    def record_processing_error(self, subscription: str) -> None:
        self.get_stats(subscription).record_processing_error()

    def record_error(self, subscription: str) -> None:
        self.get_stats(subscription).record_error()

    def get_health_status(
        self,
        ams_enabled: bool = True,
        poll_threshold_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not ams_enabled:
            return {"status": "disabled", "consumers": {}}

        consumer_reports = {}
        all_alive = True
        all_polled_recently = True
        has_errors = False

        threshold = (
            poll_threshold_seconds
            if poll_threshold_seconds is not None
            else getattr(settings, "AMS_POLL_INTERVAL", 30) * 4
        )
        now = datetime.now(timezone.utc)

        # Ensure all registered tasks/consumers are present
        all_subscriptions = set(self._consumers.keys()) | set(self._tasks.keys())

        for sub in sorted(all_subscriptions):
            stats = self.get_stats(sub)
            task = self._tasks.get(sub)
            is_cancelling = hasattr(task, "cancelling") and bool(task.cancelling())
            alive = (
                task is not None
                and not task.done()
                and not task.cancelled()
                and not is_cancelling
            )

            if not alive:
                all_alive = False

            if stats.last_successful_poll is None:
                all_polled_recently = False
            else:
                elapsed = (now - stats.last_successful_poll).total_seconds()
                if elapsed > threshold:
                    all_polled_recently = False

            if stats.consecutive_errors > 3:
                has_errors = True

            consumer_reports[sub] = stats.to_dict(alive=alive)

        # if not consumer_reports:
        #     overall_status = "unhealthy"
        # elif not all_alive:
        #     overall_status = "unhealthy"
        # elif not all_polled_recently or has_errors:
        #     overall_status = "degraded"
        # else:
        #     overall_status = "healthy"

        if not consumer_reports:
            overall_status = "unhealthy"
        elif not all_alive or not all_polled_recently:
            overall_status = "unhealthy"
        elif has_errors:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "consumers": consumer_reports,
        }

    def clear(self) -> None:
        self._consumers.clear()
        self._tasks.clear()


# Global singleton instance
ams_health_tracker = AMSHealthTracker()
