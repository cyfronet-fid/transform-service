"""Connect to s3"""

from functools import cache

import boto3
from boto3.session import Session


@cache
def connect_to_s3(access_key: str, secret_key: str, endpoint: str) -> boto3.client:
    """Connect to S3 with a singleton per credentials"""
    session = Session()
    return session.client(
        service_name="s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=str(endpoint),
    )
