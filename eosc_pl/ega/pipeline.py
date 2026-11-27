import argparse
import json
import logging
from pathlib import Path

import requests

from eosc_pl.ecudo.sender import send_to_solr
from eosc_pl.ega.mappings.best_access_right import access_map
from eosc_pl.ega.schemas.output import EgaOutput
from eosc_pl.ega.settings import URL
from eosc_pl.transform.utils.print_data_sources import print_data_sources_summary

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

with open(BASE_DIR / "datasets.json") as f:
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


def run_pipeline(
    dataset_ids: list[str] | None = None,
    dry_run: bool = False,
    output_path: Path | str | None = None,
    limit: int | None = None,
):
    logger.info("Starting EGA pipeline")
    ids = list(dataset_ids or DATASETS_IDS)
    if limit is not None and limit > 0:
        ids = ids[:limit]

    outputs: list[dict] = []
    for dataset_id in ids:
        logger.info("Processing dataset %s", dataset_id)
        try:
            raw = fetch_dataset(dataset_id)
            record = transform_to_ega_output(raw)
            outputs.append(record.model_dump())
        except Exception as e:
            logger.error("Failed for %s: %s", dataset_id, e)

    # Data sources summary
    print_data_sources_summary(
        repository_name="EGA",
        datasets=outputs,
        primary_datasource_pids=["eosc.ega.ega"],
    )

    # Save to file
    out_file = (
        Path(output_path)
        if output_path
        else PROJECT_ROOT / "eosc_pl" / "output" / "ega.json"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d transformed records to %s", len(outputs), out_file)

    # Send to Solr / dry-run
    if dry_run:
        logger.info("Dry-run active: skipped sending to Solr.")
    else:
        logger.info("Sending %d records to Solr", len(outputs))
        send_to_solr(outputs)

    logger.info("EGA pipeline completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="EGA Solr pipeline")
    parser.add_argument(
        "--dry-run",
        "--skip-solr",
        action="store_true",
        help="Skip sending transformed records to Solr and save output to JSON file",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=None,
        help="Maximum number of dataset IDs to fetch",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to save the output JSON file (defaults to eosc_pl/output/ega.json)",
    )
    parser.add_argument(
        "dataset_ids",
        nargs="*",
        default=None,
        help="Optional dataset accession IDs (defaults to datasets.json)",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        logger.error("Invalid number of records: %s", args.limit)
        return

    run_pipeline(
        dataset_ids=args.dataset_ids or None,
        dry_run=args.dry_run,
        output_path=args.output,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
