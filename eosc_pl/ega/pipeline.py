import json
import logging
from pathlib import Path

import requests
from ecudo.sender import send_to_solr
from ega.mappings.best_access_right import access_map
from ega.schemas.output import EgaOutput
from ega.settings import URL

with open("datasets.json") as f:
    DATASETS_IDS = json.load(f)["datasets_ids"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_dataset(dataset_id: str) -> dict:
    url = f"{URL}/{dataset_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def transform_to_ega_output(raw: dict) -> EgaOutput:
    access_raw = raw.get("access_type")
    dataset_id = raw.get("accession_id")

    return EgaOutput(
        id=dataset_id,
        title=raw.get("title"),
        description=raw.get("description"),
        best_access_right=access_map.get(access_raw),
        publication_date=raw.get("released_date"),
        document_type=raw.get("dataset_types"),
        technologies=raw.get("technologies"),
        num_samples=raw.get("num_samples"),
        is_in_beacon=raw.get("is_in_beacon"),
        is_released=raw.get("is_released"),
        is_deprecated=raw.get("is_deprecated"),
        policy_accession_id=raw.get("policy_accession_id"),
        url=[f"https://ega-archive.org/datasets/{dataset_id}"],
    )


def run_pipeline(load_from: Path = None, dataset_ids=None):
    logger.info("Starting EGA pipeline")
    outputs: list[dict] = []

    for dataset_id in dataset_ids:
        logger.info("Processing dataset %s", dataset_id)
        try:
            raw = fetch_dataset(dataset_id)
            record = transform_to_ega_output(raw)
            outputs.append(record.model_dump())
        except Exception as e:
            logger.error("Failed for %s: %s", dataset_id, e)

    logger.info("Sending %d records to Solr", len(outputs))
    send_to_solr(outputs)
    logger.info("Mission complete")


if __name__ == "__main__":
    run_pipeline(dataset_ids=DATASETS_IDS)
