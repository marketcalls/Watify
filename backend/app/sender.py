"""Job runner: walks a SendJob's contacts and dispatches one message at a time.

This is the function APScheduler calls. It owns its own DB session, picks
a random delay per recipient within [min_delay_s, max_delay_s], queues the
send into the wars worker, records a SendAttempt, and updates job status.

The function must be importable by string — APScheduler stores
`("app.sender:run_send_job", args=(job_id,))` in the SQLAlchemy jobstore
and re-imports it on next start, so do not move or rename without a
migration.
"""

import logging
import random
import time
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.db import engine
from app.models import (
    AttemptStatus,
    Contact,
    JobStatus,
    SendAttempt,
    SendJob,
)
from app.whatsapp import WaSingleton

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def run_send_job(job_id: int) -> None:
    log.info("send_job %s: started", job_id)
    with Session(engine) as s:
        job = s.get(SendJob, job_id)
        if job is None:
            log.warning("send_job %s: not found", job_id)
            return
        if job.status == JobStatus.cancelled:
            log.info("send_job %s: cancelled before start", job_id)
            return

        job.status = JobStatus.running
        job.started_at = _now()
        s.add(job)
        s.commit()
        s.refresh(job)

        contacts = list(
            s.exec(
                select(Contact)
                .where(Contact.group_id == job.group_id)
                .order_by(Contact.created_at)
            ).all()
        )

        # Persist all attempts as pending up front so the UI can see them.
        pending: list[SendAttempt] = []
        for c in contacts:
            a = SendAttempt(
                job_id=job.id, contact_id=c.id, status=AttemptStatus.pending
            )
            s.add(a)
            pending.append(a)
        s.commit()
        for a in pending:
            s.refresh(a)

        any_failed = False
        for attempt, contact in zip(pending, contacts):
            # Honor cancellation between attempts.
            current = s.get(SendJob, job_id)
            if current is None or current.status == JobStatus.cancelled:
                log.info("send_job %s: cancelled mid-flight", job_id)
                break

            lo = max(1, job.min_delay_s)
            hi = max(lo, job.max_delay_s)
            delay = random.uniform(lo, hi)
            log.info(
                "send_job %s: contact %s delay=%.1fs",
                job_id,
                contact.id,
                delay,
            )
            time.sleep(delay)

            snap = WaSingleton.snapshot()
            if snap.state != "ready":
                attempt.status = AttemptStatus.failed
                attempt.error = f"wa_not_ready:{snap.state}"
                any_failed = True
            else:
                try:
                    WaSingleton.send_to(contact.phone_e164, job.message)
                    attempt.status = AttemptStatus.sent
                    attempt.sent_at = _now()
                except Exception as e:  # noqa: BLE001
                    attempt.status = AttemptStatus.failed
                    attempt.error = str(e)[:512]
                    any_failed = True

            s.add(attempt)
            s.commit()

        # Final status
        job = s.get(SendJob, job_id)
        if job is None:
            return
        if job.status == JobStatus.cancelled:
            pass
        else:
            job.status = JobStatus.failed if any_failed else JobStatus.completed
        job.finished_at = _now()
        s.add(job)
        s.commit()
    log.info("send_job %s: finished", job_id)
