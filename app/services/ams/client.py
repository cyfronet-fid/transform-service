import asyncio
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List, Optional

import aiohttp

from app.services.ams.health import ams_health_tracker
from app.settings import settings
from app.transform.live_update.process_message import process_message

logger = logging.getLogger(__name__)

# Thread pool for running sync functions
executor = ThreadPoolExecutor(max_workers=10)


class MessageRetryTracker:
    """Tracks delivery/retry attempts for AMS messages to prevent infinite redelivery loops."""

    def __init__(self, max_size: int = 10000):
        self._attempts: dict[str, int] = {}
        self._max_size = max_size

    def increment(self, message_id: str) -> int:
        if len(self._attempts) >= self._max_size and message_id not in self._attempts:
            old_keys = list(self._attempts.keys())[:1000]
            for k in old_keys:
                self._attempts.pop(k, None)
        current = self._attempts.get(message_id, 0) + 1
        self._attempts[message_id] = current
        return current

    def get_attempts(self, message_id: str) -> int:
        return self._attempts.get(message_id, 0)

    def reset(self, message_id: str) -> None:
        self._attempts.pop(message_id, None)

    def clear(self) -> None:
        self._attempts.clear()


retry_tracker = MessageRetryTracker()


def _headers():
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": settings.AMS_API_TOKEN,
    }


# ------------------------------------------------------------
# SUBSCRIPTION MANAGEMENT
# ------------------------------------------------------------
async def ensure_subscription(topic: str, subscription: str):
    url = (
        f"{settings.AMS_API_BASE_URL}/projects/"
        f"{settings.AMS_PROJECT_NAME}/subscriptions/{subscription}"
    )

    payload = {
        "topic": f"projects/{settings.AMS_PROJECT_NAME}/topics/{topic}",
        "ackDeadlineSeconds": 60,
    }

    logger.info(f"[AMS] Ensuring pull subscription exists: {subscription}")

    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=payload, headers=_headers()) as resp:
            text = await resp.text()

            if resp.status == 200 or resp.status == 201:
                logger.info(f"[AMS] Subscription ready: {subscription}")
                return

            if resp.status == 409:
                logger.info(f"[AMS] Subscription already exists: {subscription}")
                return

            logger.error(
                f"[AMS] Subscription setup error for '{subscription}': status={resp.status} response={text}"
            )
            raise RuntimeError(f"[AMS] Subscription error: {resp.status} -> {text}")


# ------------------------------------------------------------
# POLLING
# ------------------------------------------------------------
async def pull_messages(subscription: str):
    project = settings.AMS_PROJECT_NAME
    url = (
        f"{settings.AMS_API_BASE_URL}/projects/"
        f"{project}/subscriptions/{subscription}:pull"
    )

    logger.debug(f"[AMS] Pulling from: {url}")

    payload = {
        "maxMessages": str(settings.AMS_PULL_MAX_MESSAGES),
        "returnImmediately": "true",  # Always return immediately instead of long-polling
    }

    # Shorter timeout since we're not long-polling
    timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_connect=10, sock_read=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=_headers()) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(
                        f"[AMS] Pull failed for subscription={subscription}: HTTP {resp.status} -> {text}"
                    )
                    ams_health_tracker.record_poll_error(subscription)
                    return []

                data = await resp.json()
                messages = data.get("receivedMessages", [])
                ams_health_tracker.record_poll_success(
                    subscription, count=len(messages)
                )

                if messages:
                    logger.info(
                        f"[AMS] Received {len(messages)} messages from subscription={subscription}"
                    )
                else:
                    logger.debug(
                        f"[AMS] Poll succeeded for {subscription}, 0 messages received."
                    )

                return messages
    except Exception as e:
        logger.error(
            f"[AMS] Exception during pull for subscription={subscription}: {e}",
            exc_info=True,
        )
        ams_health_tracker.record_poll_error(subscription)
        return []


async def ack_messages(subscription: str, ack_ids: List[str]):
    """
    Ack processed messages.
    """
    if not ack_ids:
        return

    project = settings.AMS_PROJECT_NAME
    url = (
        f"{settings.AMS_API_BASE_URL}/projects/"
        f"{project}/subscriptions/{subscription}:acknowledge"
    )

    logger.debug(
        f"[AMS] Acknowledging {len(ack_ids)} messages for subscription={subscription}"
    )
    payload = {"ackIds": ack_ids}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=_headers()) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(
                        f"[AMS] ACK failed for subscription={subscription}: HTTP {resp.status} -> {text}"
                    )
                    return False

                logger.info(
                    f"[AMS] Successfully acknowledged {len(ack_ids)} messages for subscription={subscription}"
                )
                return True
    except Exception as e:
        logger.error(
            f"[AMS] Exception during ACK for subscription={subscription}: {e}",
            exc_info=True,
        )
        return False


# ------------------------------------------------------------
# DEAD-LETTER QUEUE (DLQ) & FAILURE POLICY
# ------------------------------------------------------------
async def publish_to_dlq(
    topic: str,
    subscription: str,
    raw_data: Optional[str],
    original_message: dict,
    error_reason: str,
) -> bool:
    """
    Publishes a failed message to a dead-letter queue (DLQ) topic in AMS.
    """
    project = settings.AMS_PROJECT_NAME
    url = f"{settings.AMS_API_BASE_URL}/projects/{project}/topics/{topic}:publish"

    if raw_data:
        try:
            base64.b64decode(raw_data)
            b64_data = raw_data
        except Exception:
            b64_data = base64.b64encode(str(raw_data).encode("utf-8")).decode("utf-8")
    else:
        b64_data = base64.b64encode(b"{}").decode("utf-8")

    payload = {
        "messages": [
            {
                "attributes": {
                    "origin_subscription": str(subscription),
                    "error_reason": str(error_reason),
                    "original_ack_id": str(original_message.get("ackId", "")),
                    "message_id": str(
                        original_message.get("message", {}).get("messageId", "")
                    ),
                    "timestamp": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                },
                "data": b64_data,
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=_headers()) as resp:
                if resp.status in (200, 201):
                    logger.info(
                        f"[AMS] Successfully published failed message {original_message.get('ackId')} to DLQ topic '{topic}'"
                    )
                    return True
                text = await resp.text()
                logger.error(
                    f"[AMS] Failed to publish message to DLQ topic '{topic}': HTTP {resp.status} -> {text}"
                )
                return False
    except Exception as e:
        logger.error(
            f"[AMS] Exception while publishing message to DLQ topic '{topic}': {e}",
            exc_info=True,
        )
        return False


async def _handle_message_failure(
    subscription: str,
    ack_id: str,
    message_id: str,
    raw_data: Optional[str],
    original_message: dict,
    error_reason: str,
    ack_ids: List[str],
) -> None:
    """
    Handles processing failure for an AMS message.
    Increments delivery attempts and either leaves the message for retry or,
    if max attempts are reached, forwards it to DLQ (if configured) and ACKs it.
    """
    ams_health_tracker.record_processing_error(subscription)
    attempts = retry_tracker.increment(message_id)
    max_attempts = getattr(settings, "AMS_MAX_DELIVERY_ATTEMPTS", 5)

    if attempts >= max_attempts:
        logger.critical(
            f"[AMS] Message id={message_id} in subscription={subscription} reached max delivery "
            f"attempts ({attempts}/{max_attempts}). Error: {error_reason}. Routing to dead-letter policy."
        )
        dlq_topic = getattr(settings, "AMS_DLQ_TOPIC", None)
        if dlq_topic:
            await publish_to_dlq(
                topic=dlq_topic,
                subscription=subscription,
                raw_data=raw_data,
                original_message=original_message,
                error_reason=f"Exceeded max delivery attempts ({attempts}): {error_reason}",
            )
        # ACK to remove poison message from the subscription queue
        ack_ids.append(ack_id)
        retry_tracker.reset(message_id)
    else:
        logger.warning(
            f"[AMS] Message id={message_id} failed in subscription={subscription} "
            f"(attempt {attempts}/{max_attempts}). Error: {error_reason}. Will NOT ACK (left for retry)."
        )


# ------------------------------------------------------------
# CONSUMER LOOP
# ------------------------------------------------------------
async def ams_consume_loop(subscription: str):
    """
    Continuous consumer that polls AMS every interval.
    """
    logger.info(f"[AMS] Starting poll loop for subscription={subscription}")

    while True:
        try:
            messages = await pull_messages(subscription)

            if not messages:
                logger.debug(
                    f"[AMS] No messages received for subscription={subscription}, waiting {settings.AMS_POLL_INTERVAL}s"
                )
                await asyncio.sleep(settings.AMS_POLL_INTERVAL)
                continue

            ack_ids = []
            failed_count = 0

            for m in messages:
                ack_id = m.get("ackId")
                if not ack_id:
                    logger.warning(
                        "[AMS] Message missing ackId in subscription=%s", subscription
                    )
                    continue

                msg_obj = m.get("message", {})
                message_id = msg_obj.get("messageId") or ack_id
                raw_data = msg_obj.get("data")

                if not raw_data:
                    logger.warning(
                        "[AMS] Message missing data field in subscription=%s, ack_id=%s",
                        subscription,
                        ack_id,
                    )
                    await _handle_message_failure(
                        subscription=subscription,
                        ack_id=ack_id,
                        message_id=message_id,
                        raw_data=None,
                        original_message=m,
                        error_reason="Missing data field in message",
                        ack_ids=ack_ids,
                    )
                    failed_count += 1
                    continue

                try:
                    decoded = base64.b64decode(raw_data).decode("utf-8")
                    logger.info(
                        "[AMS] Decoded message for subscription=%s: %s...",
                        subscription,
                        decoded[:150],
                    )

                    # Run sync function in thread pool to avoid blocking async loop.
                    # Pass both decoded message and subscription name (or ack_id)
                    loop = asyncio.get_running_loop()
                    success = await loop.run_in_executor(
                        executor, process_message, decoded, subscription
                    )
                    if success:
                        retry_tracker.reset(message_id)
                        ams_health_tracker.record_message_processed(subscription)
                        logger.info(
                            "[AMS] Successfully processed message for subscription=%s, ack_id=%s",
                            subscription,
                            ack_id,
                        )
                        ack_ids.append(ack_id)
                    else:
                        await _handle_message_failure(
                            subscription=subscription,
                            ack_id=ack_id,
                            message_id=message_id,
                            raw_data=raw_data,
                            original_message=m,
                            error_reason="process_message returned False (transformation or Solr update failure)",
                            ack_ids=ack_ids,
                        )
                        failed_count += 1

                except base64.binascii.Error as e:
                    logger.error(
                        "[AMS] Base64 decode error in subscription=%s: %s",
                        subscription,
                        e,
                    )
                    await _handle_message_failure(
                        subscription=subscription,
                        ack_id=ack_id,
                        message_id=message_id,
                        raw_data=raw_data,
                        original_message=m,
                        error_reason=f"Base64 decode error: {e}",
                        ack_ids=ack_ids,
                    )
                    failed_count += 1
                except UnicodeDecodeError as e:
                    logger.error(
                        "[AMS] UTF-8 decode error in subscription=%s: %s",
                        subscription,
                        e,
                    )
                    await _handle_message_failure(
                        subscription=subscription,
                        ack_id=ack_id,
                        message_id=message_id,
                        raw_data=raw_data,
                        original_message=m,
                        error_reason=f"UTF-8 decode error: {e}",
                        ack_ids=ack_ids,
                    )
                    failed_count += 1
                except Exception as e:
                    logger.error(
                        "[AMS] Processing error in subscription=%s: %s",
                        subscription,
                        e,
                        exc_info=True,
                    )
                    await _handle_message_failure(
                        subscription=subscription,
                        ack_id=ack_id,
                        message_id=message_id,
                        raw_data=raw_data,
                        original_message=m,
                        error_reason=f"Unexpected processing exception: {e}",
                        ack_ids=ack_ids,
                    )
                    failed_count += 1

            # Acknowledge only successfully processed messages
            if ack_ids:
                success = await ack_messages(subscription, ack_ids)
                if not success:
                    logger.warning(
                        "[AMS] Failed to acknowledge messages for subscription=%s",
                        subscription,
                    )

            if failed_count > 0:
                logger.warning(
                    "[AMS] %s messages failed processing in subscription=%s and were not acknowledged",
                    failed_count,
                    subscription,
                )

        except asyncio.TimeoutError:
            logger.debug(
                f"[AMS] Timeout during poll cycle for subscription={subscription}"
            )
            await asyncio.sleep(settings.AMS_POLL_INTERVAL)
            continue

        except Exception as e:
            logger.exception(
                f"[AMS] Unexpected loop error for subscription={subscription}: {e}"
            )
            ams_health_tracker.record_poll_error(subscription)
            await asyncio.sleep(5)
