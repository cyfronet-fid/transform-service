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


async def start_ams_subscription():
    if not settings.AMS_SUBSCRIPTION:
        logger.info(
            "[AMS] Subscription disabled in settings (settings.AMS_SUBSCRIPTION=False)."
        )
        return

    logger.info(
        f"[AMS] Preparing pull subscriptions for topics: {settings.AMS_TOPICS}..."
    )

    for full_topic in settings.AMS_TOPICS:
        # "/projects/eosc-beyond-providers/topics/adapter-update"
        topic = full_topic.split("/")[-1]

        if topic not in AMS_SUBSCRIPTION_MAP:
            logger.warning(
                f"[AMS] No subscription mapping found for topic '{topic}'. Skipping."
            )
            continue

        subscription_name = AMS_SUBSCRIPTION_MAP[topic]

        logger.info(f"[AMS] Using subscription {subscription_name} for topic {topic}")

        try:
            await ensure_subscription(topic, subscription_name)
            task = asyncio.create_task(ams_consume_loop(subscription_name))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
            ams_health_tracker.register_consumer(subscription_name, task)
            logger.info(
                f"[AMS] Started consumer task for subscription '{subscription_name}'"
            )
        except Exception as e:
            logger.error(
                f"[AMS] Failed to initialize subscription '{subscription_name}' for topic '{topic}': {e}",
                exc_info=True,
            )
            ams_health_tracker.record_error(subscription_name)

    logger.info("[AMS] All requested subscriptions initialized.")
