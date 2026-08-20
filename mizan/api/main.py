"""MIZAN API application entry point.

FastAPI application that registers all route modules under /api/v1.

Start with:
    uvicorn mizan.api.main:app --reload --host 0.0.0.0 --port 8000

Or via the Makefile:
    make dev
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mizan import __version__
from mizan.api.routes import (
    certificates_route,
    datasets_route,
    evaluations_route,
    evidence_route,
    health,
    models_route,
    use_cases_route,
    websocket_route,
)
from mizan.engine.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the database on startup and clean up on shutdown."""
    await init_db()
    yield


app = FastAPI(
    title="MIZAN API",
    description=(
        "Sovereign AI Model Registry and Adaptive Compliance Engine. "
        "Version of the UAE AI Governance Framework evaluation infrastructure."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Allow the Vite dev server (port 5173) to call the API during development.
# Restrict origins appropriately in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PREFIX = "/api/v1"

app.include_router(health.router,              prefix=_PREFIX)
app.include_router(models_route.router,        prefix=_PREFIX)
app.include_router(use_cases_route.router,     prefix=_PREFIX)
app.include_router(datasets_route.router,      prefix=_PREFIX)
app.include_router(evaluations_route.router,   prefix=_PREFIX)
app.include_router(evidence_route.router,      prefix=_PREFIX)
app.include_router(certificates_route.router,  prefix=_PREFIX)
app.include_router(websocket_route.router,     prefix=_PREFIX)
