"""
sender.py
Handles sending transformed records to Solr.
"""

from itertools import islice

import requests
from ecudo import settings


def chunk_iterable(iterable, size):
    """Yield successive chunks from iterable of given size."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


def send_batch_to_solr(docs, collection):
    """Send a batch of documents to Solr via /update endpoint."""
    if not docs:
        return True
    url = f"{settings.SOLR_URL}/solr/{collection}/update?commit=true"
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json=docs, timeout=60)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send batch to {collection}: {e}")
        if "resp" in locals():
            print(f"Solr response: {resp.text}")
        return False


def send_to_solr(transformed_records):
    """Send all transformed records to all configured Solr collections in batches."""
    total = len(transformed_records)
    print(f"Sending {total} records to Solr...")
    for collection in settings.SOLR_COLLECTION_LIST:
        print(f"Sending to Solr collection: {collection}")
        for batch in chunk_iterable(transformed_records, settings.BATCH_SIZE):
            success = send_batch_to_solr(batch, collection)
            if not success:
                print(f"Some records failed for {collection}")
        print(f"Finished sending to collection: {collection}")
