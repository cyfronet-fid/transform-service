#!/usr/bin/env python3
import argparse
import logging
import shutil
import sys
from pathlib import Path

from oai_pmh import settings
from oai_pmh.common.logging_conf import setup_logging
from oai_pmh.harvester import harvest_to_ndjson
from oai_pmh.sender import send_to_solr_collections

setup_logging()
logger = logging.getLogger("pipeline")


def main():
    parser = argparse.ArgumentParser(description="OAI-PMH → Solr pipeline")
    parser.add_argument(
        "repository",
        nargs="?",
        default=settings.DEFAULT_REPOSITORY,
        help="Repository to harvest from (e.g. 'onedata')",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=settings.DEFAULT_MAX_RECORDS,
        help="Maximum number of records to harvest",
    )
    args = parser.parse_args()

    if args.repository == "onedata":
        from oai_pmh.onedata.harvest_config import METADATA_PREFIX, OAI_BASE_URL

        logger.info(f"Starting harvesting for repository: {args.repository}")
        written, full_path, dc_path = harvest_to_ndjson(
            base_url=OAI_BASE_URL,
            metadataPrefix=METADATA_PREFIX,
            max_records=args.max_records or settings.DEFAULT_MAX_RECORDS,
        )
        logger.info(f"Harvest completed. {written} records written to {dc_path}")

        if written == 0:
            logger.warning("No records harvested. Nothing will be sent to Solr.")
            sys.exit(0)

        logger.info("Starting Solr upload")
        send_to_solr_collections(dc_path)
        logger.info("Upload completed successfully")

        output_dir = Path(dc_path).parent
        try:
            shutil.rmtree(output_dir)
            logger.info(f"Deleted output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to delete output directory {output_dir}: {e}")

        logger.info("Pipeline finished successfully.")


if __name__ == "__main__":
    main()
