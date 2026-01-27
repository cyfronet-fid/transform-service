"""A celery task for sending data to solr/s3"""

import json
import logging

import boto3
from pandas import DataFrame as PandasDF
from pyspark.sql import DataFrame as SparkDF

from app.services.celery.task import CeleryTaskStatus
from app.services.celery.task_statuses import FAILURE, SUCCESS
from app.services.s3.send import s3_send_gz_data
from app.services.s3.utils import compress_to_gz
from app.services.solr.collections import COL_UPLOAD_CONFIG
from app.services.solr.send import send_str_to_solr
from app.settings import settings
from app.tasks.utils.s3_paths import extract_after_bucket
from app.worker import celery

logger = logging.getLogger(__name__)


@celery.task(name="send_data")
def send_data(
    df: SparkDF | PandasDF,
    collection_name: str,
    s3_client: boto3.client = None,
    req_body: dict = None,
    file_path: str = None,
    prev_task_status: dict = None,
) -> dict:
    """Task to send data to solr/s3"""
    if prev_task_status and prev_task_status.get("status") != SUCCESS:
        logger.error(
            "Previous task failed or missing:  %s. Skipping sending data...",
            prev_task_status,
        )
        return CeleryTaskStatus(
            status=FAILURE, reason="Previous task status failed or missing"
        ).dict()

    logger.info(
        "Starting data sending task for file: %s, collection: %s",
        file_path,
        collection_name,
    )

    try:
        if req_body:  # Dump
            send_dump_data(df, collection_name, req_body, file_path, s3_client)
        else:  # Live update
            send_live_data(df, collection_name)

        return CeleryTaskStatus(status=SUCCESS).dict()

    except Exception as e:
        logger.error(
            "Sending data failure for file: %s, collection: %s: reason: %s",
            file_path,
            collection_name,
            str(e),
        )
        return CeleryTaskStatus(status=FAILURE, reason=str(e)).dict()


def send_dump_data(
    df: SparkDF | PandasDF,
    collection_name: str,
    req_body: dict | None,
    file_path: str | None,
    s3_client: boto3.client = None,
) -> None:
    """
    Helper function to send data to S3 and/or Solr based on the task type and configuration.

    Sends serialized DataFrame data to all configured Solr and S3 instances defined
    in the request body.
    """
    if not req_body:
        logger.error("Request body is missing.")
        return

    instances = req_body.get("instances", [])
    if not instances:
        logger.warning("No instances defined in request body.")
        return

    solr_data, s3_data = serialize_df(collection_name, df)
    input_file_path = extract_after_bucket(file_path, req_body.get("dump_url", ""))

    # -------------------------
    # Handle Solr uploads
    # -------------------------
    solr_instances = [inst for inst in instances if inst.get("type") == "solr"]
    if not solr_instances:
        logger.info("No Solr instances configured.")
    else:
        for solr_instance in solr_instances:
            solr_url = solr_instance.get("url")
            solr_collections = solr_instance.get(COL_UPLOAD_CONFIG, {}).get(
                collection_name
            )

            if not solr_url or not solr_collections:
                logger.warning(
                    "Skipping Solr instance due to missing URL or collection config: %s",
                    solr_instance,
                )
                continue

            try:
                send_str_to_solr(solr_data, solr_url, solr_collections, input_file_path)
                logger.info(
                    "%s successfully sent to Solr instance at %s (collections: %s).",
                    input_file_path,
                    solr_url,
                    solr_collections,
                )
            except Exception as e:
                logger.exception(
                    "Failed to send data to Solr instance at %s (collections: %s): %s",
                    solr_url,
                    solr_collections,
                    e,
                )

    # -------------------------
    # Handle S3 uploads
    # -------------------------
    s3_instances = [inst for inst in instances if inst.get("type") == "s3"]
    if not s3_instances:
        logger.info("No S3 instances configured.")
    else:
        if not s3_client:
            logger.error("S3 client not provided but S3 instances exist.")
            raise S3ClientError()

        for s3_instance in s3_instances:
            s3_output_url = s3_instance.get("s3_output_url")
            if not s3_output_url:
                logger.warning(
                    "Skipping S3 instance with missing output URL: %s", s3_instance
                )
                continue

            try:
                s3_send_gz_data(
                    s3_data,
                    collection_name,
                    s3_output_url,
                    input_file_path,
                    s3_client,
                )
                logger.info(
                    "%s successfully sent to S3 bucket at %s.",
                    input_file_path,
                    s3_output_url,
                )
            except Exception as e:
                logger.exception(
                    "Failed to send data to S3 bucket at %s: %s",
                    s3_output_url,
                    e,
                )


def send_live_data(
    df: SparkDF | PandasDF,
    collection_name: str,
) -> None:
    """Send data to solr/s3 integrated by constant settings. Used for live update."""
    solr_data_form, s3_data_form = serialize_df(collection_name, df)
    solr_collections = settings.COLLECTIONS[collection_name]["SOLR_COL_NAMES"]
    send_str_to_solr(solr_data_form, str(settings.SOLR_URL), solr_collections)
    logger.info("Data successfully sent to Solr collections: %s.", solr_collections)


def send_merged_data(
    df: SparkDF,
    files: list[str],
    collection_name: str,
    req_body: dict,
    s3_client: boto3.client,
    prev_task_status: dict,
) -> dict:
    """Sends merged DataFrame to the target services."""
    path, file_num = get_file_number_and_path(files[0])

    if len(files) == 1:
        file_name = f"{file_num}.json.gz"
    else:
        file_range = "_to_".join(
            get_file_number_and_path(f)[1] for f in [files[0], files[-1]]
        )
        file_name = f"merged_{file_range}.json.gz"

    return send_data(
        df=df,
        collection_name=collection_name,
        s3_client=s3_client,
        req_body=req_body,
        file_path=f"{path}/{file_name}",
        prev_task_status=prev_task_status,
    )


def get_file_number_and_path(file_path: str) -> tuple[str, str]:
    """Extracts the file number and the rest of the path from the file path."""
    parts = file_path.rsplit("/", 1)  # Split into path and filename
    path, filename = parts[0], parts[1]
    file_number = filename.split(".")[0].split("-")[-1]
    return path, file_number


def serialize_df(collection_name: str, df: SparkDF | PandasDF) -> [str, bytes]:
    """Serialize dataframes to solr format (str) and s3 format (.gz)"""
    if collection_name == settings.GUIDELINE:  # Pandas
        s3_raw_json = df.apply(lambda row: row.to_json(), axis=1).tolist()
        solr_data_form = df.to_json(orient="records")
    else:  # Spark
        s3_raw_json = df.toJSON().collect()
        solr_data_form = json.dumps([json.loads(line) for line in s3_raw_json])

    compressed_s3_json = compress_to_gz(s3_raw_json)
    return solr_data_form, compressed_s3_json


class S3ClientError(Exception):
    """Exception raised when S3 client is not provided and it is needed."""

    def __init__(self, message="No S3 client provided."):
        self.message = message
        super().__init__(self.message)
