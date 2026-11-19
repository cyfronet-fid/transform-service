import asyncio
import logging

from app.services.ams.client import ams_consume_loop, ensure_subscription
from app.services.ams.health import ams_health_tracker
from app.settings import settings

logger = logging.getLogger(__name__)

AMS_SUBSCRIPTION_MAP = {
    "training_resource-create": "transformer-training_resource-create",
    "training_resource-update": "transformer-training_resource-update",
    "training_resource-delete": "transformer-training_resource-delete",
    "interoperability_record-create": "transformer-interoperability_record-create",
    "interoperability_record-update": "transformer-interoperability_record-update",
    "interoperability_record-delete": "transformer-interoperability_record-delete",
    "adapter-create": "transformer-adapter-create",
    "adapter-update": "transformer-adapter-update",
    "adapter-delete": "transformer-adapter-delete",
}

background_tasks = set()


async def run_consumer_task(
    topic: str,
    subscription_name: str,
    initial_backoff: float = 2.0,
    max_backoff: float = 60.0,
    backoff_factor: float = 2.0,
):
    backoff = initial_backoff

    while True:
        try:
            await ensure_subscription(topic, subscription_name)
            logger.info(
                "[AMS] Subscription '%s' verified for topic '%s'. Starting consume loop.",
                subscription_name,
                topic,
            )
            backoff = initial_backoff
            await ams_consume_loop(subscription_name)
        except asyncio.CancelledError:
            logger.info(
                "[AMS] Consumer task cancelled for subscription '%s'",
                subscription_name,
            )
            raise
        except Exception as e:
            logger.error(
                "[AMS] Error in consumer task for subscription '%s' (topic '%s'): %s. "
                "Retrying in %.1fs...",
                subscription_name,
                topic,
                e,
                backoff,
                exc_info=True,
            )
            ams_health_tracker.record_poll_error(subscription_name)
            await asyncio.sleep(backoff)
            backoff = min(backoff * backoff_factor, max_backoff)


async def start_ams_subscription():
    if not settings.AMS_SUBSCRIPTION:
        logger.info(
            "[AMS] Subscription disabled in settings (settings.AMS_SUBSCRIPTION=False)."
        )
        return

    logger.info(
        "[AMS] Preparing pull subscriptions for topics: %s...",
        settings.AMS_TOPICS,
    )

    for full_topic in settings.AMS_TOPICS:
        # "/projects/eosc-beyond-providers/topics/adapter-update"
        topic = full_topic.split("/")[-1]

        if topic not in AMS_SUBSCRIPTION_MAP:
            logger.warning(
                "[AMS] No subscription mapping found for topic '%s'. Skipping.",
                topic,
            )
            continue

        subscription_name = AMS_SUBSCRIPTION_MAP[topic]
        ams_health_tracker.register_consumer(subscription_name)

        logger.info(
            "[AMS] Spawning supervised consumer for subscription %s (topic %s)",
            subscription_name,
            topic,
        )

        task = asyncio.create_task(run_consumer_task(topic, subscription_name))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        ams_health_tracker.set_task(subscription_name, task)

    logger.info("[AMS] All requested subscriptions initialized.")


async def stop_ams_subscription():
    """
    Cancel and wait for all running AMS consumer tasks to shut down.
    """
    logger.info("[AMS] Stopping %s AMS consumer tasks...", len(background_tasks))
    tasks = list(background_tasks)
    for task in tasks:
        task.cancel()

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    background_tasks.clear()
    logger.info("[AMS] All AMS consumer tasks stopped.")
