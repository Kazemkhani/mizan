"""Database engine configuration, session management, and evidence write path.

The connection string is read from the MIZAN_DATABASE_URL environment
variable. The default is a SQLite file at data/mizan.db relative to the
repository root, which is appropriate for the demo.

To switch to Postgres, set:
    MIZAN_DATABASE_URL=postgresql+asyncpg://user:pass@host/mizan

No other code changes are required for session management; the schema is
Postgres-compatible by design (see engine/db/schema.sql). The
append_evidence() function currently targets SQLite only; the Postgres
path is marked SOVEREIGN-TODO for Wave 3.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

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

def canonical_payload(payload: dict) -> str:
    """Serialise a payload dict to its canonical JSON form.

    The canonical form is compact JSON with keys sorted lexicographically
    and all Unicode characters preserved (ensure_ascii=False). This is the
    single authorised serialisation for evidence payloads. Any caller that
    serialises the dict independently risks producing a different byte
    sequence, which will appear as a hash mismatch when
    scripts/verify_evidence.py recomputes SHA-256(stored_payload).

    HARNESS must pass payload dicts through append_evidence() and must
    never supply a pre-serialised string or a payload_hash of its own.

    scripts/verify_evidence.py verifies by computing SHA-256 of the
    stored payload string directly; it does not re-serialise. This
    function is therefore the only place where the serialisation format
    is defined.
    """
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


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


# ---------------------------------------------------------------------------
# Evidence write path
# The only sanctioned way to insert a row into the evidence table.
# ---------------------------------------------------------------------------

def _append_evidence_sync(
    db_path: str,
    *,
    ev_id: str,
    evaluation_id: str,
    suite_id: str,
    control_id: str,
    probe_id: str,
    payload: dict,
    score: float,
    passed: int,
    collected_at: str,
) -> tuple[str, str]:
    """Synchronous core of append_evidence(). Runs in a thread via asyncio.to_thread().

    Serialises the payload via canonical_payload(), computes payload_hash,
    looks up the current chain tail for this evaluation, and inserts one row.
    Raises sqlite3.IntegrityError on any trigger or constraint violation; the
    caller (append_evidence) distinguishes UNIQUE fork collisions from hard
    failures and retries accordingly.
    """
    text_payload = canonical_payload(payload)
    h = sha256_of(text_payload)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        # The tail of the hash chain is the most recently inserted row for
        # this evaluation. ORDER BY rowid is reliable under SQLite's
        # serialised write model; a new insert always gets the highest rowid.
        row = conn.execute(
            "SELECT payload_hash FROM evidence "
            "WHERE evaluation_id = ? ORDER BY rowid DESC LIMIT 1",
            (evaluation_id,),
        ).fetchone()
        chain_prev = row[0] if row else ""

        conn.execute(
            """
            INSERT INTO evidence
                (id, evaluation_id, suite_id, control_id, probe_id,
                 payload, payload_hash, chain_prev_hash, score, passed, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ev_id, evaluation_id, suite_id, control_id, probe_id,
                text_payload, h, chain_prev, score, passed, collected_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return ev_id, h


async def append_evidence(
    *,
    evaluation_id: str,
    suite_id: str,
    control_id: str,
    probe_id: str,
    payload: dict,
    score: float,
    passed: int,
    max_retries: int = 3,
) -> tuple[str, str]:
    """Append one evidence row to an evaluation's append-only log.

    This is the only sanctioned write path for the evidence table. HARNESS
    must use this function exclusively; raw INSERT statements against the
    evidence table are prohibited.

    Callers supply a structured payload dict. This function:
      1. Serialises the dict canonically via canonical_payload().
      2. Computes payload_hash = sha256_of(canonical_string).
      3. Looks up and sets chain_prev_hash automatically.
      4. Inserts the row through the database triggers.

    Callers cannot supply a payload_hash or chain_prev_hash. Removing
    those parameters from the interface eliminates the attack surface that
    the F0-01 audit finding (Attack 4) identified: a caller who computes
    the hash incorrectly would produce a row that the verify script
    reports as compromised. See docs/DECISIONS.md D-015.

    Concurrency:
    If two callers race on the same evaluation_id, both may read the same
    chain tail hash in the SELECT and both attempt INSERT with the same
    chain_prev_hash. The UNIQUE index on (evaluation_id, chain_prev_hash)
    ensures only one succeeds. The loser receives a UNIQUE constraint
    error and this function retries automatically, re-reading the updated
    tail on each attempt.

    Returns:
        (ev_id, payload_hash): the UUID of the new row and its hash.

    Raises:
        RuntimeError: if max_retries consecutive UNIQUE collisions occur.
        sqlite3.IntegrityError: if a trigger hard-blocks the insert (e.g.
            the evaluation_id does not exist, the hash chain is broken by
            a non-fork cause).
        NotImplementedError: if MIZAN_DATABASE_URL points to Postgres
            (Wave 3 SOVEREIGN-TODO).
    """
    if "sqlite" not in _DATABASE_URL:
        # SOVEREIGN-TODO: implement Postgres path in Wave 3.
        # On Postgres, payload_hash is a generated column; the application
        # layer computes and verifies it, but the database enforces it via
        # the generated expression. The retry logic is identical; replace
        # the sqlite3.IntegrityError check with asyncpg.UniqueViolationError.
        raise NotImplementedError(
            "append_evidence: Postgres path not yet implemented (Wave 3)"
        )

    db_path = _DATABASE_URL.split("///", 1)[1]
    now = datetime.now(timezone.utc).isoformat()

    for attempt in range(max_retries):
        ev_id = str(uuid4())
        try:
            return await asyncio.to_thread(
                _append_evidence_sync,
                db_path,
                ev_id=ev_id,
                evaluation_id=evaluation_id,
                suite_id=suite_id,
                control_id=control_id,
                probe_id=probe_id,
                payload=payload,
                score=score,
                passed=passed,
                collected_at=now,
            )
        except sqlite3.IntegrityError as exc:
            msg = str(exc)
            if "UNIQUE constraint failed" in msg and "chain" in msg:
                # Two concurrent callers both read the same tail hash and
                # raced to insert the next link. The loser retries with a
                # fresh tail read in the next iteration of this loop.
                if attempt < max_retries - 1:
                    continue
            # Any other IntegrityError (trigger RAISE, FK violation, etc.)
            # is a hard failure; re-raise immediately.
            raise

    raise RuntimeError(
        f"append_evidence: {max_retries} consecutive UNIQUE fork collisions on "
        f"evaluation '{evaluation_id}'. Another writer may be appending "
        "continuously. Investigate concurrent harness processes."
    )
