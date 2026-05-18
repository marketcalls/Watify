import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.db import init_db
from app.logging_setup import configure as configure_logging
from app.routers import groups, jobs, whatsapp
from app.scheduler import shutdown as scheduler_shutdown
from app.scheduler import start as scheduler_start
from app.settings import settings

log = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("watify starting version=%s", __version__)
    init_db()
    scheduler_start()
    try:
        yield
    finally:
        scheduler_shutdown()
        log.info("watify stopped")


app = FastAPI(title="Watify", version=__version__, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error path=%s method=%s", request.url.path, request.method)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": exc.__class__.__name__},
    )


app.include_router(groups.router)
app.include_router(whatsapp.router)
app.include_router(jobs.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "watify", "version": __version__}
