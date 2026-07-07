from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    audit,
    auth,
    cds,
    dashboard,
    integrations,
    medication_catalog,
    medications,
    patients,
    prescriptions,
    users,
)
from app.core.config import settings
from app.database.seed import seed_demo_data
from app.database.session import SessionLocal, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    if settings.auto_seed:
        db = SessionLocal()
        try:
            seed_demo_data(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.7.0",
    description="API educacional para apoio demonstrativo à prescrição segura.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(patients.router, prefix=settings.api_prefix)
app.include_router(medications.router, prefix=settings.api_prefix)
app.include_router(medication_catalog.router, prefix=settings.api_prefix)
app.include_router(prescriptions.router, prefix=settings.api_prefix)
app.include_router(cds.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(integrations.router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
