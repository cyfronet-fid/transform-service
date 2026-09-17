"""A task for transforming a batch of data and sending it to solr"""

import json
import logging
from typing import Optional

import app.transform.transformers as trans
from app.services.celery.task import CeleryTaskStatus
from app.services.celery.task_statuses import FAILURE, SUCCESS
from app.services.solr.delete import delete_data_by_type
from app.services.spark.config import apply_spark_conf
from app.settings import settings
from app.tasks.utils.send import send_data
from app.transform.utils.load import load_request_data
from app.worker import celery

logger = logging.getLogger(__name__)


@celery.task(name="transform_batch")
def transform_batch(
    type_: str,
    data: dict | list[dict],
    full_update=True,
) -> dict | None:
    """Celery task for transforming batch data

    Args:
        type_ (str): Data type
        data (dict): Data
        full_update (bool): Is it a full collection update?
    """
    item_count = len(data) if isinstance(data, list) else 1
    logger.info(
        f"[TransformBatch] Transformation started for type='{type_}', full_update={full_update}, items_count={item_count}"
    )

    transformer = trans.transformers.get(type_)

    if not transformer:
        logger.error(
            f"[TransformBatch] No data transformer is provided for type='{type_}'"
        )
        return CeleryTaskStatus(
            status=FAILURE, reason=f"No data transformer is provided for {type_}"
        ).dict()

    # Transform
    try:
        if type_ == settings.GUIDELINE:  # Pandas
            logger.info(
                f"[TransformBatch] Executing Pandas transformation for type='{type_}'"
            )
            df_trans = transformer(data)
        else:  # Pyspark
            logger.info(
                f"[TransformBatch] Applying Spark configuration for type='{type_}'"
            )
            spark, _ = apply_spark_conf()
            input_schema = settings.COLLECTIONS.get(type_, {}).get("INPUT_SCHEMA")
            logger.info(
                f"[TransformBatch] Loading and validating request data against schema for type='{type_}'"
            )
            df = load_request_data(spark, data, input_schema, type_)
            logger.info(
                f"[TransformBatch] Data loaded into PySpark DataFrame. Applying transformer for type='{type_}'"
            )
            df_trans = transformer(spark)(df)

        if full_update:
            # Delete all resources of a certain type only if that is a full collection update
            delete_data_by_type(type_)

        task_status = send_data(
            df=df_trans,
            collection_name=type_,
        )

        if task_status["status"] == FAILURE:
            raise Exception(task_status["reason"], "Unknown error")

        logger.info(f"{type_} data update has been successful")
        return CeleryTaskStatus(status=SUCCESS).dict()

    except Exception as e:
        logger.error(
            f"[TransformBatch] Transformation failed for type='{type_}', full_update={full_update}. Error: {e}",
            exc_info=True,
        )
        return CeleryTaskStatus(status=FAILURE, reason=str(e)).dict()
