import asyncio
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List

import aiohttp

from app.services.ams.health import ams_health_tracker
from app.settings import settings
from app.transform.live_update.process_message import process_message

logger = logging.getLogger(__name__)

# Thread pool for running sync functions
executor = ThreadPoolExecutor(max_workers=10)


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
        "ackDeadlineSeconds": 10,
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
                    ams_health_tracker.record_error(subscription)
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
        ams_health_tracker.record_error(subscription)
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
                        f"[AMS] Message missing ackId in subscription={subscription}"
                    )
                    continue

                ack_ids.append(ack_id)
                raw_data = m.get("message", {}).get("data")

                if not raw_data:
                    logger.warning(
                        f"[AMS] Message missing data field in subscription={subscription}, ack_id={ack_id}"
                    )
                    continue

                try:
                    decoded = base64.b64decode(raw_data).decode("utf-8")
                    logger.info(
                        f"[AMS] Decoded message for subscription={subscription}: {decoded[:150]}..."
                    )

                    # Run sync function in thread pool to avoid blocking async loop.
                    # Pass both decoded message and subscription name (or ack_id)
                    await asyncio.get_event_loop().run_in_executor(
                        executor, process_message, decoded, subscription
                    )
                    ams_health_tracker.record_message_processed(subscription)
                    logger.info(
                        f"[AMS] Successfully processed message for subscription={subscription}, ack_id={ack_id}"
                    )

                except base64.binascii.Error as e:
                    logger.error(
                        f"[AMS] Base64 decode error in subscription={subscription}: {e}"
                    )
                    ams_health_tracker.record_error(subscription)
                    failed_count += 1
                except UnicodeDecodeError as e:
                    logger.error(
                        f"[AMS] UTF-8 decode error in subscription={subscription}: {e}"
                    )
                    ams_health_tracker.record_error(subscription)
                    failed_count += 1
                except Exception as e:
                    logger.error(
                        f"[AMS] Processing error in subscription={subscription}: {e}",
                        exc_info=True,
                    )
                    ams_health_tracker.record_error(subscription)
                    failed_count += 1

            # Acknowledge all processed messages (even failed ones, to not block the subscription)
            if ack_ids:
                success = await ack_messages(subscription, ack_ids)
                if not success:
                    logger.warning(
                        f"[AMS] Failed to acknowledge messages for subscription={subscription}"
                    )

                if failed_count > 0:
                    logger.warning(
                        f"[AMS] {failed_count}/{len(ack_ids)} messages failed processing in subscription={subscription}"
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
            ams_health_tracker.record_error(subscription)
            await asyncio.sleep(5)
