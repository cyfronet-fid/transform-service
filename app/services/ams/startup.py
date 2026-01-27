import asyncio
import logging

from app.services.ams.client import ams_consume_loop, ensure_subscription
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


async def start_ams_subscription():
    if not settings.AMS_SUBSCRIPTION:
        logger.info("[AMS] Subscription disabled.")
        return

    logger.info("[AMS] Preparing pull subscriptions...")

    for full_topic in settings.AMS_TOPICS:
        # "/projects/eosc-beyond-providers/topics/adapter-update"
        topic = full_topic.split("/")[-1]

        subscription_name = AMS_SUBSCRIPTION_MAP[topic]

        logger.info(f"[AMS] Using subscription {subscription_name} for topic {topic}")

        await ensure_subscription(topic, subscription_name)
        asyncio.create_task(ams_consume_loop(subscription_name))

    logger.info("[AMS] All subscriptions active.")
