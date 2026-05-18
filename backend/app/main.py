import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.auth_middleware import AuthMiddleware
from app.csrf_middleware import CSRFMiddleware
from app.db import init_db
from app.identity import fingerprint as app_fingerprint
from app.identity import is_configured as identity_configured
from app.limiter import limiter, rate_limit_handler
from app.logging_setup import configure as configure_logging
from app.routers import auth, groups, jobs, whatsapp
from app.scheduler import shutdown as scheduler_shutdown
from app.scheduler import start as scheduler_start
from app.settings import settings

log = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("watify starting version=%s", __version__)
    # TKT-0031: surface identity status at boot so the operator
    # immediately sees whether auth endpoints will refuse to operate.
    if identity_configured():
        log.info("watify identity: app_secret configured (fingerprint=%s)", app_fingerprint())
    else:
        log.warning(
            "watify identity: WATIFY_APP_SECRET is empty -- auth endpoints will "
            "return 503 auth_not_configured. Run install/install.sh or generate "
            "manually: `openssl rand -hex 32`."
        )
    init_db()
    scheduler_start()
    try:
        yield
    finally:
        scheduler_shutdown()
        log.info("watify stopped")


app = FastAPI(title="Watify", version=__version__, lifespan=lifespan)

# TKT-0015: slowapi rate-limit on send endpoints. Wired here so the
# limiter sees the FastAPI app early; route decorators in
# routers/whatsapp.py and routers/jobs.py reference `app.limiter`.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TKT-0025: AuthMiddleware registered AFTER CORS so it sits OUTERMOST
# in Starlette's middleware stack (FastAPI applies middleware in
# reverse order of add_middleware). Auth gate runs first on every
# request; slowapi decorators wrap the handler itself, so rate limits
# stay INSIDE the gate -- a 429 can never disclose token validity.
app.add_middleware(AuthMiddleware)

# TKT-0032: CSRFMiddleware registered AFTER AuthMiddleware so it sits
# OUTERMOST. On a state-changing /api/* request the order is:
# CSRF -> Auth -> CORS -> handler. A forged unauthenticated POST is
# rejected 403 csrf_required before it ever reaches the auth check,
# which is fine -- both gates would reject the request anyway, and
# this layering keeps the CSRF concern self-contained.
app.add_middleware(CSRFMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Flatten HTTPException.detail into a top-level body.

    FastAPI's default wraps everything under `{"detail": ...}`. The
    frontend wants flat error envelopes per REQUIREMENTS S2; this
    handler maps:
      detail=dict        -> dict body, inject `error` if missing
      detail=str         -> {"error": detail, "detail": detail}
      detail=anything    -> {"error": "http_error", "detail": detail}
    RequestValidationError (Pydantic 422) is left to FastAPI's default
    so the per-field error list keeps its standard shape.
    """
    detail = exc.detail
    if isinstance(detail, dict):
        body: dict = dict(detail)
        body.setdefault("error", "http_error")
    elif isinstance(detail, str):
        body = {"error": detail, "detail": detail}
    else:
        body = {"error": "http_error", "detail": detail}
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error path=%s method=%s", request.url.path, request.method)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": exc.__class__.__name__},
    )


app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(whatsapp.router)
app.include_router(jobs.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "watify",
        "version": __version__,
        # TKT-0031: stable 8-char identifier for the installed app_secret.
        # Null when unconfigured so the operator can spot the missing
        # secret with one curl. The full secret never leaves the box.
        "app_fingerprint": app_fingerprint(),
    }
