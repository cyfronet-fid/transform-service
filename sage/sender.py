import os
from itertools import islice
from logging import getLogger

import requests
from dotenv import load_dotenv


logger = getLogger(__name__)

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


def delete_all_from_solr():
    """Delete all documents from the Solr collection."""
    url = f"{SOLR_URL}/solr/{SOLR_COLLECTION}/update?commit=true"
    headers = {"Content-Type": "application/json"}

    logger.info(
        "Deleting all documents from Solr collection '%s'",
        SOLR_COLLECTION,
    )

    try:
        response = requests.post(
            url,
            json={"delete": {"query": "*:*"}},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        logger.info(
            "Successfully deleted all documents from Solr collection '%s'",
            SOLR_COLLECTION,
        )

        return True

    except requests.RequestException as exc:
        logger.error(
            "Failed to delete documents from Solr collection '%s': %s",
            SOLR_COLLECTION,
            exc,
        )

        if "response" in locals():
            logger.error("Solr response: %s", response.text)

        return False

    except Exception:
        logger.exception(
            "Unexpected error while deleting documents from Solr"
        )
        return False


def send_batch_to_solr(docs):
    """Send a batch of documents to Solr."""
    if not docs:
        logger.debug("Skipping empty Solr batch")
        return True

    url = f"{SOLR_URL}/solr/{SOLR_COLLECTION}/update?commit=true"
    headers = {"Content-Type": "application/json"}

    logger.debug(
        "Sending batch of %d documents to Solr collection '%s'",
        len(docs),
        SOLR_COLLECTION,
    )

    try:
        response = requests.post(
            url,
            json=docs,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        logger.debug(
            "Successfully sent batch of %d documents to Solr",
            len(docs),
        )

        return True

    except requests.RequestException as exc:
        logger.error(
            "Solr update failed for batch of %d documents: %s",
            len(docs),
            exc,
        )

        if "response" in locals():
            logger.error("Solr response: %s", response.text)

        return False

    except Exception:
        logger.exception(
            "Unexpected error while sending batch of %d documents to Solr",
            len(docs),
        )
        return False


def send_to_solr(all_docs):
    """Send all records to Solr in batches."""
    total = len(all_docs)

    if not total:
        logger.warning("No documents to send to Solr")
        return False

    logger.info(
        "Sending %d records to Solr collection '%s' in batches of %d",
        total,
        SOLR_COLLECTION,
        BATCH_SIZE,
    )

    successful_batches = 0
    failed_batches = 0
    sent_documents = 0

    for batch_number, batch in enumerate(
        chunk_iterable(all_docs, BATCH_SIZE),
        start=1,
    ):
        logger.debug(
            "Processing Solr batch %d with %d documents",
            batch_number,
            len(batch),
        )

        ok = send_batch_to_solr(batch)

        if ok:
            successful_batches += 1
            sent_documents += len(batch)

            logger.info(
                "Successfully sent Solr batch %d: %d documents",
                batch_number,
                len(batch),
            )
        else:
            failed_batches += 1

            logger.error(
                "Solr batch %d failed: %d documents",
                batch_number,
                len(batch),
            )

    success = failed_batches == 0

    logger.info(
        "Solr indexing finished: %d/%d documents sent successfully, "
        "%d successful batches, %d failed batches",
        sent_documents,
        total,
        successful_batches,
        failed_batches,
    )

    return success
