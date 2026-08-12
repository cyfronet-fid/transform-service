import hashlib
import json
from logging import getLogger

from sage.client import AggregatorClient
from sage.logging_config import configure_logging
from sage.sender import delete_all_from_solr, send_to_solr
from sage.state import get_checksum, save_checksum
from sage.transfomer import transform_raw_dataset

logger = getLogger(__name__)


def calculate_checksum(datasets):
    """
    Calculate a deterministic checksum for the dataset snapshot.

    Dataset order does not affect the checksum.

    The dynamically generated ODRL policy ID is excluded because
    the Aggregator may generate a different value for the same
    dataset between requests.
    """
    normalized = []

    for dataset in datasets:
        dataset_copy = json.loads(json.dumps(dataset))

        policy = dataset_copy.get("odrl:hasPolicy")

        if isinstance(policy, dict):
            policy.pop("@id", None)

        normalized.append(dataset_copy)

    normalized.sort(
        key=lambda dataset: dataset.get("@id", ""),
    )

    serialized = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    logger.debug(
        "Calculated dataset checksum: %s",
        checksum,
    )

    return checksum


def flatten_datasets(catalogs):
    """
    Extract all raw dataset dicts from EDC catalogs.

    Handles both:
    - a single dataset object: "dcat:dataset": {...}
    - a list of datasets: "dcat:dataset": [{...}, {...}]
    """
    datasets = []

    if not isinstance(catalogs, list):
        logger.error(
            "Expected list of catalog objects, got %s",
            type(catalogs).__name__,
        )
        return datasets

    logger.debug(
        "Processing %d catalog objects",
        len(catalogs),
    )

    for catalog in catalogs:
        raw_datasets = catalog.get(
            "dcat:dataset",
            [],
        )

        if isinstance(raw_datasets, dict):
            logger.debug("Found a single dataset object in catalog")
            raw_datasets = [raw_datasets]

        if not isinstance(raw_datasets, list):
            logger.warning(
                "Unexpected dcat:dataset type: %s",
                type(raw_datasets).__name__,
            )
            continue

        for dataset in raw_datasets:
            if not isinstance(dataset, dict):
                logger.warning(
                    "Skipping dataset with unexpected type: %s",
                    type(dataset).__name__,
                )
                continue

            dataset["catalogue"] = catalog.get("dspace:participantId") or ""
            dataset["participant_id"] = catalog.get("dspace:participantId")
            dataset["originator"] = catalog.get("originator")

            datasets.append(dataset)

    logger.info(
        "Flattened %d datasets from %d catalogs",
        len(datasets),
        len(catalogs),
    )

    return datasets


def main():
    logger.info("Starting metadata pipeline")

    # 1. Fetch current snapshot from Aggregator
    logger.info("Fetching catalog data from Aggregator")

    client = AggregatorClient()
    data = client.fetch_catalog()

    logger.debug(
        "Received catalog response of type: %s",
        type(data).__name__,
    )

    # 2. Flatten catalogs into datasets
    raw_datasets = flatten_datasets(data)

    logger.info(
        "Total raw datasets: %d",
        len(raw_datasets),
    )

    if not raw_datasets:
        logger.warning("No datasets found in Aggregator response")
        return

    # 3. Calculate checksum of current snapshot
    current_checksum = calculate_checksum(raw_datasets)
    previous_checksum = get_checksum()

    logger.debug(
        "Previous checksum: %s",
        previous_checksum,
    )
    logger.debug(
        "Current checksum: %s",
        current_checksum,
    )

    # 4. Skip Solr update if nothing changed
    if current_checksum == previous_checksum:
        logger.info("No changes detected in Aggregator data. " "Skipping Solr update.")
        return

    logger.info(
        "Changes detected in Aggregator data. "
        "Current checksum: %s, previous checksum: %s",
        current_checksum,
        previous_checksum,
    )

    # 5. Transform the complete snapshot BEFORE touching Solr
    logger.info(
        "Transforming %d datasets",
        len(raw_datasets),
    )

    transformed = []

    for dataset in raw_datasets:
        transformed_dataset = transform_raw_dataset(dataset)

        if transformed_dataset is not None:
            transformed.append(transformed_dataset)

    logger.info(
        "Successfully transformed %d/%d datasets",
        len(transformed),
        len(raw_datasets),
    )

    if not transformed:
        logger.error(
            "No datasets were successfully transformed. " "Keeping existing Solr data."
        )
        return

    # 6. Only now modify Solr
    logger.info(
        "Replacing existing Solr snapshot with %d datasets",
        len(transformed),
    )

    deleted = delete_all_from_solr()

    if not deleted:
        logger.error("Failed to clear Solr collection. " "Aborting pipeline.")
        return

    # 7. Index the new snapshot
    indexed = send_to_solr(transformed)

    if not indexed:
        logger.error(
            "Failed to index the new Solr snapshot. " "Checksum will NOT be updated."
        )
        return

    # 8. Only save checksum after successful indexing
    save_checksum(current_checksum)

    logger.info(
        "Metadata pipeline finished successfully. "
        "Indexed %d datasets and saved checksum %s",
        len(transformed),
        current_checksum,
    )


if __name__ == "__main__":
    configure_logging()
    main()
