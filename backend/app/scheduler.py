"""APScheduler singleton.

Backed by a SQLAlchemyJobStore on `app.db` so scheduled jobs survive a
backend restart. One scheduler per process — matches the wars
single-process constraint (see wars.md §7).
"""

import logging
from typing import Optional

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.db import DATABASE_URL

log = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(
            jobstores={
                "default": SQLAlchemyJobStore(
                    url=DATABASE_URL, tablename="apscheduler_jobs"
                )
            },
            timezone="UTC",
        )
    return _scheduler


def start() -> None:
    s = get_scheduler()
    if not s.running:
        s.start()
        log.info("scheduler started")


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("scheduler shut down")


def aps_job_id(send_job_id: int) -> str:
    return f"send_job_{send_job_id}"
