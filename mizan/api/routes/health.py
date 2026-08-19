"""Health check endpoint.

GET /api/v1/health

Returns the application version and database connectivity status. This
endpoint is used by the Makefile dev target to confirm the API is ready
before launching the web shell.
"""

from __future__ import annotations

from fastapi import APIRouter

from mizan import __version__
from mizan.api.schemas import HealthOut
from mizan.engine.db.database import engine

router = APIRouter()


@router.get("/health", response_model=HealthOut, tags=["system"])
async def health() -> HealthOut:
    """Return API health and database connectivity status."""
    db_status: str = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthOut(version=__version__, database=db_status)  # type: ignore[arg-type]
