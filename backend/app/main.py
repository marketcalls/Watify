from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.db import init_db
from app.routers import groups, jobs, whatsapp
from app.scheduler import shutdown as scheduler_shutdown
from app.scheduler import start as scheduler_start


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler_start()
    try:
        yield
    finally:
        scheduler_shutdown()


app = FastAPI(title="Watify", version=__version__, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(groups.router)
app.include_router(whatsapp.router)
app.include_router(jobs.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "watify", "version": __version__}
