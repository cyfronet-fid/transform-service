"""S3 send module."""

import logging
import os

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

from app.services.s3.utils import extract_bucket_and_key

logger = logging.getLogger(__name__)


def s3_send_gz_data(
    gz_data: bytes,
    col_name: str,
    s3_output_url: str,
    input_file_path: str,
    s3: boto3.client,
) -> None:
    """
    Send compressed data to S3 output URL.

    Args:
        gz_data (io.BytesIO): Compressed (.gz) file-like object to be uploaded.
        col_name (str): Collection name. E.g. 'dataset'.
        s3_output_url (str): The S3 output dump URL - where data should be stored.
        input_file_path (str): input file path.
        s3 (boto3.client): Boto3 S3 client.

    Raises:
        ClientError: If there is an error during the S3 upload.
        EndpointConnectionError: If there is a connectivity issue with the S3 endpoint.
    """
    bucket, output_file_path = extract_bucket_and_key(s3_output_url)
    filename = os.path.basename(input_file_path)  # Extract filename from the path
    if not filename.endswith(".gz"):
        filename += ".gz"
    file_path = f"{output_file_path}/{col_name}/{filename}"

    try:
        s3.upload_fileobj(
            Fileobj=gz_data,
            Bucket=bucket,
            Key=file_path,
        )
        logger.info(f"{input_file_path} successfully uploaded to {file_path}")
    except (ClientError, EndpointConnectionError) as err:
        # TODO failed_files[col_name][S3].append(file)
        logger.error(f"{input_file_path} failed to be sent to the S3 - {err}")
