from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.responses import JSONResponse, Response

from hirein_api.db import create_engine, create_session_factory
from hirein_api.evals.routes import router as evals_router
from hirein_api.evidence.routes import router as evidence_router
from hirein_api.jobs.routes import router as jobs_router
from hirein_api.profile.routes import router as profile_router
from hirein_api.security import valid_backend_token, valid_ingestion_token
from hirein_api.settings import load_settings

settings = load_settings()
engine = create_engine(settings)
session_factory = create_session_factory(engine)


class HealthResponse(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="HireIn API",
    version="0.5.0",
    description="Core API for the HireIn single-user pilot.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-HireIn-Pilot-Token",
        "X-HireIn-Ingestion-Token",
    ],
)

CallNext = Callable[[Request], Awaitable[Response]]


@app.middleware("http")
async def protect_pilot_api(request: Request, call_next: CallNext) -> Response:
    if request.url.path.startswith("/api/v1/"):
        provided = request.headers.get("x-hirein-pilot-token")
        authorized = valid_backend_token(settings.pilot_backend_token, provided)

        is_job_ingestion = (
            request.method.upper() == "POST"
            and request.url.path.rstrip("/") == "/api/v1/jobs"
        )
        if not authorized and is_job_ingestion:
            ingestion_token = request.headers.get("x-hirein-ingestion-token")
            authorized = valid_ingestion_token(
                settings.job_ingestion_token,
                ingestion_token,
            )

        if not authorized:
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
    return await call_next(request)


app.include_router(profile_router)
app.include_router(jobs_router)
app.include_router(evals_router)
app.include_router(evidence_router)


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
async def liveness(response: Response) -> HealthResponse:
    # Intentionally independent from the database and downstream services.
    # External uptime probes may call this endpoint frequently.
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def readiness(request: Request) -> HealthResponse:
    db_engine: AsyncEngine = request.app.state.engine
    try:
        async with db_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc

    return HealthResponse(status="ok")


app.state.engine = engine
app.state.session_factory = session_factory
