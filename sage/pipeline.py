"""Metadata pipeline for SAGE project."""

import json
import logging

from sage.client import AggregatorClient
from sage.sender import send_to_solr
from sage.transfomer import transform_raw_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def flatten_datasets(catalogs):
    """
    Extract all raw dataset dicts from EDC catalogs.

    Handles both:
    - a single dataset object: "dcat:dataset": {...}
    - a list of datasets: "dcat:dataset": [{...}, {...}]
    """
    datasets = []

    if not isinstance(catalogs, list):
        logger.error("Expected list of catalog objects, got %s", type(catalogs).__name__)
        return datasets

    logger.debug("Processing %d catalog objects", len(catalogs))

    for catalog in catalogs:
        raw_datasets = catalog.get("dcat:dataset", [])

        # Aggregator may return a single dataset as a dict
        if isinstance(raw_datasets, dict):
            logger.debug("Found a single dataset object in catalog")
            raw_datasets = [raw_datasets]

        # Ignore unexpected values
        if not isinstance(raw_datasets, list):
            logger.warning(
                "Unexpected dcat:dataset type: %s",
                type(raw_datasets).__name__,
            )
            continue

        logger.debug("Found %d datasets in catalog", len(raw_datasets))

        for dataset in raw_datasets:
            if not isinstance(dataset, dict):
                logger.warning(
                    "Skipping dataset with unexpected type: %s",
                    type(dataset).__name__,
                )
                continue

            dataset["catalogue"] = (
                catalog.get("dspace:participantId") or ""
            )
            dataset["participant_id"] = catalog.get("dspace:participantId")
            dataset["originator"] = catalog.get("originator")

            datasets.append(dataset)

    logger.info("Flattened %d datasets from %d catalogs", len(datasets), len(catalogs))

    return datasets


def main():
    logger.info("Starting metadata pipeline")

    # 1) Load all catalogs from EDC
    logger.info("Fetching catalog data from Aggregator")

    client = AggregatorClient()
    data = client.fetch_catalog()

    logger.debug(
        "Received catalog response of type: %s",
        type(data).__name__,
    )

    # 2) Flatten catalogs into dataset list
    raw_datasets = flatten_datasets(data)

    logger.info("Total raw datasets: %d", len(raw_datasets))

    if not raw_datasets:
        logger.warning("No datasets found in Aggregator response")
        return

    # 3) Transform datasets
    logger.info("Transforming %d datasets", len(raw_datasets))

    transformed = [
        transformed_dataset
        for transformed_dataset in (
            transform_raw_dataset(dataset)
            for dataset in raw_datasets
        )
        if transformed_dataset is not None
    ]

    logger.info("Transformed datasets: %d", len(transformed))

    # 4) Show one example
    if raw_datasets:
        logger.debug(
            "Sample raw record:\n%s",
            json.dumps(raw_datasets[0], indent=2),
        )

    if transformed:
        logger.debug(
            "Sample transformed record:\n%s",
            json.dumps(transformed[0], indent=2),
        )

    # 5) Send to Solr
    if transformed:
        logger.info("Sending %d datasets to Solr", len(transformed))
        send_to_solr(transformed)
        logger.info("Datasets successfully sent to Solr")
    else:
        logger.warning("No datasets available to send to Solr")

    logger.info("Metadata pipeline finished")


if __name__ == "__main__":
    main()
