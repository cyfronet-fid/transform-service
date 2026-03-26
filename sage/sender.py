import os
from itertools import islice

import requests
from dotenv import load_dotenv

load_dotenv()

SOLR_URL = os.getenv("SOLR_URL")
SOLR_COLLECTION = os.getenv("SOLR_COLS_NAME")
BATCH_SIZE = 200


def chunk_iterable(iterable, size):
    """Yield chunks of size N from iterable."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


def send_batch_to_solr(docs):
    """Send a batch of documents to Solr."""
    if not docs:
        return True

    url = f"{SOLR_URL}/solr/{SOLR_COLLECTION}/update?commit=true"
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, json=docs, headers=headers, timeout=30)
        resp.raise_for_status()
        return True

    except Exception as e:
        print(f"[ERROR] Solr update failed: {e}")
        if "resp" in locals():
            print("Solr response:", resp.text)
        return False


def send_to_solr(all_docs):
    """Send all records to Solr in batches."""
    total = len(all_docs)
    print(f"Sending {total} records to Solr collection '{SOLR_COLLECTION}'...")

    for batch in chunk_iterable(all_docs, BATCH_SIZE):
        ok = send_batch_to_solr(batch)
        if not ok:
            print("[WARN] Some batches failed")
        else:
            print(f"✓ Sent batch of {len(batch)} records")

    print("Done.")
