"""Runs the SAGE pipeline on a configurable schedule."""

from logging import getLogger

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from sage.logging_config import configure_logging
from sage.pipeline import main as run_pipeline
from sage.settings import settings

logger = getLogger(__name__)


def run_pipeline_safely() -> None:
    """Run the SAGE pipeline and prevent scheduler shutdown on failure."""
    logger.info("Starting scheduled SAGE pipeline run")

    try:
        run_pipeline()
    except Exception:
        logger.exception("SAGE pipeline run failed")


def main() -> None:
    configure_logging()

    interval_minutes = settings.scheduler_interval_minutes

    logger.info(
        "Starting SAGE scheduler with interval of %d minutes",
        interval_minutes,
    )

    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        run_pipeline_safely,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="sage_pipeline",
        replace_existing=True,
    )

    logger.info(
        "SAGE scheduler started. First pipeline run will occur " "after %d minutes.",
        interval_minutes,
    )

    scheduler.start()


if __name__ == "__main__":
    main()
