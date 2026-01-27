#!/usr/bin/env python3
import json
import logging
from pathlib import Path

import requests
from oai_pmh import settings
from oai_pmh.common.utils import chunk_iterable, load_ndjson
from tqdm import tqdm

logger = logging.getLogger(__name__)


def send_batch_to_solr(docs, collection):
    """Send a batch of documents to Solr via the /update endpoint."""
    if not docs:
        return True

    url = f"{settings.SOLR_URL}/solr/{collection}/update?commit=true"
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, json=docs, timeout=60)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send batch to {collection}: {e}")
        if "resp" in locals():
            logger.error(f"Solr response: {resp.text}")
        return False


def send_to_solr_collections(path):
    """Send all records from an NDJSON file to all configured Solr collections."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"NDJSON file not found: {path}")

    records = list(load_ndjson(path_obj))
    total = len(records)
    logger.info(f"Found {total} records to send from {path}")

    for collection in settings.SOLR_COLLECTION_LIST:
        logger.info(f"Sending to Solr collection: {collection}")
        for batch in tqdm(
            chunk_iterable(records, settings.BATCH_SIZE),
            total=(total // settings.BATCH_SIZE) + 1,
        ):
            success = send_batch_to_solr(batch, collection)
            if not success:
                logger.warning(f"Some records failed for {collection}")
        logger.info(f"Finished sending to collection: {collection}")
