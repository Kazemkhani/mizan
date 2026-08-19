"""Database engine configuration and session management.

The connection string is read from the MIZAN_DATABASE_URL environment
variable. The default is a SQLite file at data/mizan.db relative to the
repository root, which is appropriate for the demo.

To switch to Postgres, set:
    MIZAN_DATABASE_URL=postgresql+asyncpg://user:pass@host/mizan

No other code changes are required; the schema is Postgres-compatible by
design (see engine/db/schema.sql).
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Repository root is three levels up from this file:
# mizan/engine/db/database.py -> mizan/engine/db -> mizan/engine -> mizan -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_PATH = _REPO_ROOT / "engine" / "db" / "schema.sql"
_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "mizan.db"

# Ensure the data directory exists so the SQLite file can be created.
_DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_DATABASE_URL = os.environ.get(
    "MIZAN_DATABASE_URL",
    f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}",
)

engine = create_async_engine(
    _DATABASE_URL,
    echo=False,
    # SQLite-specific: allow sharing across threads for async use.
    # Ignored for Postgres.
    connect_args={"check_same_thread": False} if "sqlite" in _DATABASE_URL else {},
)

_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, committing on success and rolling back on error."""
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def init_db_sync() -> None:
    """Initialise the SQLite database synchronously using the stdlib sqlite3 module.

    This is intentionally synchronous: DDL initialisation is a once-at-startup
    operation and using stdlib sqlite3 avoids the async driver complexity while
    guaranteeing correct multi-statement DDL execution via executescript().

    For Postgres: this function is a no-op. Schema migration for Postgres is
    handled externally (e.g., via Alembic or psql -f engine/db/schema.sql).
    """
    if "sqlite" not in _DATABASE_URL:
        # SOVEREIGN-TODO: add Postgres migration runner in Wave 3.
        return

    ddl = _SCHEMA_PATH.read_text(encoding="utf-8")
    db_path = str(_DEFAULT_DB_PATH)
    with sqlite3.connect(db_path) as conn:
        # executescript() handles multi-statement DDL including semicolons
        # inside SQL line comments, which a naive split cannot handle.
        # It issues an implicit COMMIT before execution.
        conn.executescript(ddl)


async def init_db() -> None:
    """Initialise the database schema.

    Delegates to init_db_sync() for SQLite. This function is kept async so
    the call site (lifespan handler) does not need to distinguish database types.
    """
    init_db_sync()


# ---------------------------------------------------------------------------
# Content-addressing utilities
# Used by the evidence layer to compute and verify SHA-256 payload hashes.
# ---------------------------------------------------------------------------

def sha256_of(payload: str) -> str:
    """Return the hex-encoded SHA-256 digest of a UTF-8 encoded string."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evidence_bundle_hash(payload_hashes: list[str]) -> str:
    """Compute the bundle hash for a certificate.

    The bundle hash is SHA-256 of the concatenation of all evidence
    payload_hash values for an evaluation, sorted lexicographically.
    This is deterministic and independent of insertion order.
    """
    combined = "".join(sorted(payload_hashes))
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
