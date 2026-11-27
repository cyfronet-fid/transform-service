import argparse
import json
import logging.config
import subprocess
import sys
from pathlib import Path

from app.logger import LOGGING_CONFIG
from eosc_pl.ecudo import settings
from eosc_pl.transform.utils.print_data_sources import print_data_sources_summary

from .sender import send_to_solr

logging.config.dictConfig(LOGGING_CONFIG)

from .schemas.output import EcudoRecord

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

logger = logging.getLogger(__name__)
DUMP_FILE = settings.OUTPUT_DIR / "ecudo_dump.json"


def run_create_dump():
    logger.info("Running create_dump to fetch fresh metadata...")
    result = subprocess.run(
        [sys.executable, "-m", "eosc_pl.ecudo.create_dump"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        logger.error("create_dump failed:\n%s", result.stderr)
        raise RuntimeError("Failed to run create_dump.py")
    logger.info("Dump created successfully.")


def load_dump(path: Path | None = None) -> list:
    path = path or DUMP_FILE
    if not path.exists():
        logger.warning("Dump file %s not found. Creating a new one...", path)
        run_create_dump()
    logger.info("Loading metadata dump from %s...", path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def transform_and_validate(records: list) -> list[dict]:
    logger.info("Transforming and validating %d records...", len(records))
    transformed = []

    for r in records:
        issued = r.get("issued")
        modified = r.get("modified")

        # Split keywords on comma if it's a string, otherwise assume list
        raw_keywords = r.get("keywords", [])
        if isinstance(raw_keywords, str):
            keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]
        elif isinstance(raw_keywords, list):
            keywords_list = raw_keywords
        else:
            keywords_list = []

        # Get distribution URL as string
        distribution_url: list[str] = []
        if isinstance(r.get("distribution"), list) and r["distribution"]:
            dist = r["distribution"][0]
            url_value = dist.get("downloadURL")
            if url_value:
                distribution_url = [str(url_value)]

        # Build Pydantic record
        record_data = EcudoRecord(
            id=r.get("identifier"),
            title=r.get("title"),
            description=r.get("description"),
            language=r.get("language"),
            publication_date=issued,
            publication_year=issued[:4] if issued else None,
            updated_at=modified,
            publisher=(
                r.get("publisher", {}).get("name")
                if isinstance(r.get("publisher"), dict)
                else None
            ),
            spatial=r.get("spatial"),
            temporal=r.get("temporal"),
            keywords=keywords_list,
            keywords_tg=keywords_list.copy(),
            url=distribution_url,
        )
        transformed.append(record_data.model_dump())
    logger.info(
        "Transformation and validation completed: %d records.", len(transformed)
    )
    return transformed


def run_pipeline(
    load_from: Path | str | None = None,
    dry_run: bool = False,
    output_path: Path | str | None = None,
    limit: int | None = None,
):
    # Load and transform
    logger.info("Running ECUDO pipeline...")
    records = load_dump(Path(load_from) if load_from else None)
    if limit is not None and limit > 0:
        records = records[:limit]
    logger.info("Found %d records to process", len(records))

    transformed_records = transform_and_validate(records)
    logger.info("Transformed %d records", len(transformed_records))

    # Data sources summary
    publishers = sorted(
        list({r.get("publisher") for r in transformed_records if r.get("publisher")})
    )

    print_data_sources_summary(
        repository_name="ECUDO",
        datasets=transformed_records,
        primary_datasource_pids=["eosc.gdansk_tech.ecudo"],
        publishers=publishers,
    )

    # Save to file
    out_file = (
        Path(output_path)
        if output_path
        else PROJECT_ROOT / "eosc_pl" / "output" / "ecudo.json"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(transformed_records, f, indent=2, ensure_ascii=False)
    logger.info(
        "Saved %d transformed records to %s", len(transformed_records), out_file
    )

    # Send to Solr / dry-run
    if dry_run:
        logger.info("Dry-run active: skipped sending to Solr.")
    else:
        logger.info("Sending %d records to Solr...", len(transformed_records))
        send_to_solr(transformed_records)

    logger.info("ECUDO pipeline finished successfully.")


def main():
    parser = argparse.ArgumentParser(description="ECUDO Solr pipeline")
    parser.add_argument(
        "--dry-run",
        "--skip-solr",
        action="store_true",
        help="Skip sending transformed records to Solr and save output to JSON file",
    )
    parser.add_argument(
        "--from-file",
        type=str,
        default=None,
        help="Path to an existing ECUDO dump JSON file",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=None,
        help="Maximum number of records to process",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to save the output JSON file (defaults to eosc_pl/output/ecudo.json)",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        logger.error("Invalid number of records: %s", args.limit)
        return

    run_pipeline(
        load_from=args.from_file,
        dry_run=args.dry_run,
        output_path=args.output,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
