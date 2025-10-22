import json
import logging
import shutil
import subprocess
from pathlib import Path

from ecudo import settings
from sender import send_to_solr

from schemas.output import EcudoRecord

logger = logging.getLogger(__name__)
DUMP_FILE = settings.OUTPUT_DIR / "ecudo_dump.json"


def run_create_dump():
    logger.info("Running create_dump to fetch fresh metadata...")
    result = subprocess.run(
        ["python", "create_dump.py"], capture_output=True, text=True
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


def run_pipeline(load_from: Path = None):
    # Load and transform
    records = load_dump(load_from)
    transformed_records = transform_and_validate(records)

    # Send to Solr
    logger.info("Sending %d records to Solr...", len(transformed_records))
    send_to_solr(transformed_records)

    # Delete raw dump folder
    output_dir = DUMP_FILE.parent
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
            logger.info("Deleted output directory: %s", output_dir)
        except Exception as e:
            logger.error("Failed to delete output directory %s: %s", output_dir, e)


if __name__ == "__main__":
    run_pipeline()
