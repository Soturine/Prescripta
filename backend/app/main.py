from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import (
    audit,
    auth,
    cds,
    dashboard,
    exports,
    integrations,
    medication_catalog,
    medications,
    patients,
    prescriptions,
    protocols,
    reports,
    users,
)
from app.api.routes import (
    settings as settings_routes,
)
from app.core.config import settings
from app.core.version import APP_VERSION
from app.database.seed import seed_demo_data
from app.database.session import SessionLocal, get_db, init_db
from app.services.ai_settings import AIConfigurationError, AISettingsService


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
    version=APP_VERSION,
    description=(
        "API educacional para apoio à prescrição segura com regras determinísticas, "
        "fontes rastreáveis, revisão humana e IA explicativa configurável."
    ),
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
app.include_router(protocols.router, prefix=settings.api_prefix)
app.include_router(cds.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(exports.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(integrations.router, prefix=settings.api_prefix)
app.include_router(settings_routes.router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
@app.get(f"{settings.api_prefix}/health", tags=["health"])
def health(db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    database_status = "ok"
    ai_provider = settings.ai_provider
    external_ai_enabled = settings.ai_enable_external_calls
    try:
        db.execute(text("SELECT 1"))
        ai_settings = AISettingsService(db).current()
        ai_provider = ai_settings.provider
        external_ai_enabled = ai_settings.enable_external_calls
    except AIConfigurationError:
        database_status = "ok"
    except Exception:  # pragma: no cover - defensive readiness path
        database_status = "error"
    return {
        "app": settings.app_name,
        "version": APP_VERSION,
        "environment": settings.environment,
        "database": database_status,
        "ai_provider": ai_provider,
        "external_ai_enabled": external_ai_enabled,
    }
