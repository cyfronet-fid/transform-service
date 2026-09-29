import logging
from typing import Literal

from fastapi import APIRouter

from app.services.mp_pc.data import get_data
from app.settings import settings
from app.tasks.transform.batch import transform_batch

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/full")
async def full_update(
    data_type: Literal[
        "all",
        "service",
        "data source",
        "provider",
        "offer",
        "bundle",
        "interoperability guideline",
        "training",
        "catalogue",
        "adapter",
        "deployable service",
    ],
) -> dict[str, str | None]:
    """Perform a full update of data collection/collections"""
    logger.info("[FullUpdate] Received request for full update: data_type=%s", data_type)

    tasks_ids = {
        settings.SERVICE: None,
        settings.DATASOURCE: None,
        settings.PROVIDER: None,
        settings.OFFER: None,
        settings.BUNDLE: None,
        settings.GUIDELINE: None,
        settings.TRAINING: None,
        settings.CATALOGUE: None,
        settings.ADAPTER: None,
        settings.DEPLOYABLE_SERVICE: None,
    }

    if data_type == "all":
        # Update all collections
        for col in (
            settings.CATALOGUE,
            settings.PROVIDER,
            settings.SERVICE,
            settings.DATASOURCE,
            settings.OFFER,
            settings.BUNDLE,
            settings.GUIDELINE,
            settings.TRAINING,
            settings.ADAPTER,
            settings.DEPLOYABLE_SERVICE,
        ):
            await update_single_col(col, tasks_ids)
    else:
        # Update single collection
        await update_single_col(data_type, tasks_ids)

    logger.info("[FullUpdate] Full update task scheduling complete. Task IDs: %s", tasks_ids)
    return tasks_ids


async def update_single_col(data_type: str, tasks_id: dict) -> None:
    """Update whole, single collection"""
    data_address = settings.COLLECTIONS[data_type]["ADDRESS"]
    logger.info(
        "[FullUpdate] Fetching full data for collection=%s from address=%s",
        data_type,
        data_address,
    )

    data = await get_data(data_type, data_address)

    if data is not None:
        record_count = len(data)
        logger.info(
            "[FullUpdate] Retrieved %s items for collection=%s. Dispatching transform_batch task...",
            record_count,
            data_type,
        )
        update_task = transform_batch.delay(data_type, data, full_update=True)
        tasks_id[data_type] = update_task.id
        logger.info(
            "[FullUpdate] Dispatched transform_batch task for collection=%s, task_id=%s",
            data_type,
            update_task.id,
        )
    else:
        error_msg = f"Retrieving data from {data_address} has failed. Please try again. Check logs for details."
        logger.error(
            "[FullUpdate] Failed to retrieve data for collection=%s from address=%s",
            data_type,
            data_address,
        )
        tasks_id[data_type] = error_msg

