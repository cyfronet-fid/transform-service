"""Calculate checksum of the Aggregator response and persist it to disk.
Why? To avoid reprocessing the same data if it hasn't changed since the last run."""

from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)

CHECKSUM_FILE = Path("sage/state/aggregator_checksum")


def get_checksum() -> str | None:
    """Get the previously stored Aggregator checksum."""
    if not CHECKSUM_FILE.exists():
        logger.debug("Checksum file does not exist: %s", CHECKSUM_FILE)
        return None

    checksum = CHECKSUM_FILE.read_text().strip()

    if not checksum:
        logger.debug("Checksum file is empty: %s", CHECKSUM_FILE)
        return None

    logger.debug("Loaded previous checksum: %s", checksum)

    return checksum


def save_checksum(checksum: str) -> None:
    """Persist the current Aggregator checksum."""
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_FILE.write_text(checksum)

    logger.debug("Saved new checksum: %s", checksum)
