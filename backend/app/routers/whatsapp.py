"""WhatsApp connection + test-send endpoints under /api/wa."""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.jid import InvalidPhoneError, normalize_phone, redact_phone
from app.limiter import limiter
from app.settings import settings
from app.whatsapp import WaSingleton

router = APIRouter(prefix="/api/wa", tags=["whatsapp"])


class WaState(BaseModel):
    state: str
    qr_data_url: str | None = None
    owner_phone: str | None = None
    last_error: str | None = None
    last_event_at: str | None = None


class WaTestSelfRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)


class WaTestToRequest(BaseModel):
    phone: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=4096)


class WaSendResult(BaseModel):
    queued: bool
    target: str  # "self" or "number"
    phone_redacted: str | None = None


def _snapshot_to_dto() -> WaState:
    snap = WaSingleton.snapshot()
    # TKT-0005: surface owner_phone in redacted form so it can be
    # displayed safely in the Ready panel (and in screenshots) without
    # exposing the full number. The full digits stay server-side.
    owner_display = redact_phone(snap.owner_phone) if snap.owner_phone else None
    return WaState(
        state=snap.state,
        qr_data_url=snap.qr_data_url,
        owner_phone=owner_display,
        last_error=snap.last_error,
        last_event_at=snap.last_event_at,
    )


@router.get("/state", response_model=WaState)
def get_state() -> WaState:
    return _snapshot_to_dto()


@router.post("/connect", response_model=WaState)
def connect() -> WaState:
    WaSingleton.connect()
    return _snapshot_to_dto()


@router.post("/disconnect", response_model=WaState)
def disconnect() -> WaState:
    WaSingleton.disconnect()
    return _snapshot_to_dto()


def _require_ready() -> None:
    snap = WaSingleton.snapshot()
    if snap.state != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "not_ready", "state": snap.state},
        )


@router.post("/test/self", response_model=WaSendResult)
@limiter.limit(settings.rate_limit_test_self)
def test_send_self(request: Request, body: WaTestSelfRequest) -> WaSendResult:
    _require_ready()
    WaSingleton.send_self(body.text)
    return WaSendResult(queued=True, target="self", phone_redacted=None)


@router.post("/test/to", response_model=WaSendResult)
@limiter.limit(settings.rate_limit_test_to)
def test_send_to(request: Request, body: WaTestToRequest) -> WaSendResult:
    _require_ready()
    try:
        phone = normalize_phone(body.phone)
    except InvalidPhoneError as e:
        raise HTTPException(status_code=422, detail=str(e))
    WaSingleton.send_to(phone, body.text)
    return WaSendResult(
        queued=True,
        target="number",
        phone_redacted=redact_phone(phone),
    )
