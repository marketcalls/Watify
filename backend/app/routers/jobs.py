"""Send-job orchestrator endpoints under /api/send and /api/jobs."""

from datetime import datetime, timezone
from typing import Literal

from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, func, select

from app.constants import DEFAULT_MAX_DELAY_S, DEFAULT_MIN_DELAY_S, MAX_DELAY_S
from app.db import get_session
from app.jid import redact_phone
from app.models import (
    AttemptStatus,
    Contact,
    FriendGroup,
    JobStatus,
    SendAttempt,
    SendJob,
)
from app.scheduler import aps_job_id, get_scheduler

router = APIRouter(tags=["send"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SendRequest(BaseModel):
    group_id: int = Field(ge=1)
    message: str = Field(min_length=1, max_length=4096)
    schedule: str = Field(default="now")  # "now" or ISO 8601
    min_delay_s: int = Field(default=DEFAULT_MIN_DELAY_S, ge=1, le=MAX_DELAY_S)
    max_delay_s: int = Field(default=DEFAULT_MAX_DELAY_S, ge=1, le=MAX_DELAY_S)

    @field_validator("max_delay_s")
    @classmethod
    def _max_ge_min(cls, v, info):
        mn = info.data.get("min_delay_s", DEFAULT_MIN_DELAY_S)
        if v < mn:
            raise ValueError("max_delay_s must be >= min_delay_s")
        return v


class JobCounts(BaseModel):
    total: int
    pending: int
    sent: int
    failed: int


class SendJobRead(BaseModel):
    id: int
    group_id: int
    group_name: str
    message_preview: str
    status: JobStatus
    scheduled_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    min_delay_s: int
    max_delay_s: int
    created_at: datetime
    counts: JobCounts


class SendAttemptRead(BaseModel):
    id: int
    contact_id: int
    contact_name: str
    contact_phone_redacted: str
    status: AttemptStatus
    sent_at: datetime | None
    error: str | None


class SendJobDetail(SendJobRead):
    message: str
    attempts: list[SendAttemptRead]


def _job_counts(session: Session, job_id: int) -> JobCounts:
    total = int(
        session.exec(
            select(func.count())
            .select_from(SendAttempt)
            .where(SendAttempt.job_id == job_id)
        ).one()
    )

    def by(s: AttemptStatus) -> int:
        return int(
            session.exec(
                select(func.count())
                .select_from(SendAttempt)
                .where(SendAttempt.job_id == job_id, SendAttempt.status == s)
            ).one()
        )

    return JobCounts(
        total=total,
        pending=by(AttemptStatus.pending),
        sent=by(AttemptStatus.sent),
        failed=by(AttemptStatus.failed),
    )


def _job_to_read(
    session: Session, job: SendJob, *, group_name: str
) -> SendJobRead:
    return SendJobRead(
        id=job.id,
        group_id=job.group_id,
        group_name=group_name,
        message_preview=(job.message[:80] + "...") if len(job.message) > 80 else job.message,
        status=job.status,
        scheduled_at=job.scheduled_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        min_delay_s=job.min_delay_s,
        max_delay_s=job.max_delay_s,
        created_at=job.created_at,
        counts=_job_counts(session, job.id),
    )


@router.post("/api/send", response_model=SendJobRead, status_code=201)
def create_send(
    body: SendRequest,
    session: Session = Depends(get_session),
) -> SendJobRead:
    group = session.get(FriendGroup, body.group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="group_not_found")

    contact_count = int(
        session.exec(
            select(func.count())
            .select_from(Contact)
            .where(Contact.group_id == body.group_id)
        ).one()
    )
    if contact_count == 0:
        raise HTTPException(status_code=422, detail="group_has_no_contacts")

    if body.schedule == "now":
        run_at = _now()
        status_val = JobStatus.pending
        scheduled_at = None
    else:
        try:
            run_at = datetime.fromisoformat(body.schedule)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="schedule must be 'now' or an ISO 8601 datetime",
            )
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)
        if run_at <= _now():
            raise HTTPException(status_code=422, detail="schedule_in_past")
        status_val = JobStatus.scheduled
        scheduled_at = run_at

    job = SendJob(
        group_id=body.group_id,
        message=body.message,
        status=status_val,
        scheduled_at=scheduled_at,
        min_delay_s=body.min_delay_s,
        max_delay_s=body.max_delay_s,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    get_scheduler().add_job(
        "app.sender:run_send_job",
        trigger=DateTrigger(run_date=run_at),
        args=[job.id],
        id=aps_job_id(job.id),
        replace_existing=True,
        misfire_grace_time=300,
    )

    return _job_to_read(session, job, group_name=group.name)


@router.get("/api/jobs", response_model=list[SendJobRead])
def list_jobs(
    session: Session = Depends(get_session),
) -> list[SendJobRead]:
    rows = session.exec(
        select(SendJob, FriendGroup)
        .join(FriendGroup, FriendGroup.id == SendJob.group_id)
        .order_by(SendJob.created_at.desc())
    ).all()
    return [_job_to_read(session, j, group_name=g.name) for j, g in rows]


@router.get("/api/jobs/{job_id}", response_model=SendJobDetail)
def get_job(
    job_id: int,
    session: Session = Depends(get_session),
) -> SendJobDetail:
    job = session.get(SendJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    group = session.get(FriendGroup, job.group_id)
    group_name = group.name if group else ""

    attempts_rows = session.exec(
        select(SendAttempt, Contact)
        .join(Contact, Contact.id == SendAttempt.contact_id)
        .where(SendAttempt.job_id == job_id)
        .order_by(SendAttempt.id)
    ).all()

    attempts = [
        SendAttemptRead(
            id=a.id,
            contact_id=a.contact_id,
            contact_name=c.name,
            contact_phone_redacted=redact_phone(c.phone_e164),
            status=a.status,
            sent_at=a.sent_at,
            error=a.error,
        )
        for a, c in attempts_rows
    ]

    base = _job_to_read(session, job, group_name=group_name)
    return SendJobDetail(
        **base.model_dump(),
        message=job.message,
        attempts=attempts,
    )


@router.delete("/api/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_job(
    job_id: int,
    session: Session = Depends(get_session),
) -> Response:
    job = session.get(SendJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
        raise HTTPException(status_code=409, detail="job_already_terminal")

    job.status = JobStatus.cancelled
    job.finished_at = _now()
    session.add(job)
    session.commit()

    try:
        get_scheduler().remove_job(aps_job_id(job_id))
    except Exception:  # noqa: BLE001 - job may have already fired
        pass

    return Response(status_code=status.HTTP_204_NO_CONTENT)
