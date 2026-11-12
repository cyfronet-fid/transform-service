#!/usr/bin/env python3
import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

from eosc_pl.oai_pmh import settings
from eosc_pl.oai_pmh.common.logging_conf import setup_logging
from eosc_pl.oai_pmh.harvester import harvest_to_ndjson
from eosc_pl.oai_pmh.sender import send_to_solr_collections

setup_logging()
logger = logging.getLogger("pipeline")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_pipeline(
    repository: str = settings.DEFAULT_REPOSITORY,
    max_records: int | None = None,
    dry_run: bool = False,
    output_path: Path | str | None = None,
):
    if repository == "onedata":
        from eosc_pl.oai_pmh.onedata.harvest_config import METADATA_PREFIX, OAI_BASE_URL

        limit = max_records or settings.DEFAULT_MAX_RECORDS
        logger.info(
            "Starting harvesting for repository: %s (max_records=%s)", repository, limit
        )
        written, full_path, dc_path = harvest_to_ndjson(
            base_url=OAI_BASE_URL,
            metadataPrefix=METADATA_PREFIX,
            max_records=limit,
        )
        logger.info("Harvest completed. %d records written to %s", written, dc_path)

        if written == 0:
            logger.warning("No records harvested. Nothing will be sent to Solr.")
            return

        # Load transformed records from NDJSON
        records = []
        with open(dc_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

        # Data sources summary
        print("\n" + "=" * 50)
        print("=== DATA SOURCES SUMMARY (OneData OAI-PMH) ===")
        print("Primary DataSource PID: ['eosc.cyfronet.onedata']")
        print(f"Total datasets harvested: {len(records)}")
        print("=" * 50 + "\n")

        # Save to output file
        out_file = (
            Path(output_path)
            if output_path
            else PROJECT_ROOT / "eosc_pl" / "output" / "onedata.json"
        )
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logger.info("Saved %d records to %s", len(records), out_file)

        # Upload / dry-run
        if dry_run:
            logger.info("Dry-run active: skipped sending to Solr.")
        else:
            logger.info("Starting Solr upload")
            send_to_solr_collections(dc_path)
            logger.info("Upload completed successfully")

        # Clean temporary harvest directory (leave the out_file intact)
        output_dir = Path(dc_path).parent
        if not dry_run and output_dir.exists() and output_dir != out_file.parent:
            try:
                shutil.rmtree(output_dir)
                logger.info("Deleted temporary harvest directory: %s", output_dir)
            except Exception as e:
                logger.error(
                    "Failed to delete temporary directory %s: %s", output_dir, e
                )

        logger.info("OAI-PMH pipeline finished successfully.")
    else:
        logger.error("Unknown repository: %s", repository)


def main():
    parser = argparse.ArgumentParser(description="OAI-PMH Solr pipeline")
    parser.add_argument(
        "repository",
        nargs="?",
        default=settings.DEFAULT_REPOSITORY,
        help="Repository to harvest from (e.g. 'onedata')",
    )
    parser.add_argument(
        "--max-records",
        "--limit",
        "-n",
        type=int,
        default=settings.DEFAULT_MAX_RECORDS,
        help="Maximum number of records to harvest",
    )
    parser.add_argument(
        "--dry-run",
        "--skip-solr",
        action="store_true",
        help="Skip sending transformed records to Solr and save output to JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to save the output JSON file (defaults to eosc_pl/output/onedata.json)",
    )
    args = parser.parse_args()

    run_pipeline(
        repository=args.repository,
        max_records=args.max_records,
        dry_run=args.dry_run,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
