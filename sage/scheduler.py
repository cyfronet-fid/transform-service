"""Runs the SAGE pipeline on a cron schedule (every 10 minutes)."""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from sage.pipeline import main as run_pipeline


def run_pipeline_safely():
    try:
        run_pipeline()
    except Exception as exc:
        print(f"[ERROR] Pipeline run failed: {exc}")


def main():
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_pipeline_safely, CronTrigger(minute="*/10"))

    print("Starting SAGE scheduler (every 10 minutes)...")
    run_pipeline_safely()  # run once immediately on startup
    scheduler.start()


if __name__ == "__main__":
    main()
