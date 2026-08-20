"""Small synchronous SQLite helpers shared by the API routes.

The data-access layer in mizan.engine.db owns the evidence write path, which
is deliberately the only way evidence enters the database. The registry
tables (models, evaluations, certificates) are ordinary records, and the
routes read and write them through the helpers here so that a restart of the
API does not lose a submitted model, which is what an in-process fixture
store did.

British English throughout.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]


def db_path() -> Path:
    """Resolve the database file, honouring MIZAN_DATABASE_URL.

    Read per call rather than captured at import, and read from the same
    environment variable the data-access layer uses, so a test that points
    the variable at a temporary file gets a hermetic database.
    """
    url = os.environ.get("MIZAN_DATABASE_URL", "")
    if url.startswith("sqlite") and "///" in url:
        return Path(url.split("///", 1)[1])
    return _REPO_ROOT / "data" / "mizan.db"


def connect() -> sqlite3.Connection:
    """Open a connection with row access by column name."""
    conn = sqlite3.connect(str(db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Run a SELECT and return the rows as dictionaries.

    The connection is closed explicitly. A sqlite3 connection used as a
    context manager commits, it does not close, and a connection left open
    holds its lock: the evaluation loop writes one evidence row per probe,
    and leaked read connections turned that into a five-second lock wait per
    probe until the run appeared to hang.
    """
    with closing(connect()) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    """Run a SELECT expected to match at most one row."""
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple = ()) -> None:
    """Run a statement that writes, committing on success."""
    with closing(connect()) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(sql, params)
        conn.commit()
