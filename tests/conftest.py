"""Shared test fixtures.

The API tests previously ran against whatever `data/mizan.db` happened to be in
the working copy. That passed locally, where the developer had just seeded and
run an evaluation, and failed on a clean checkout in continuous integration with
`no such table: use_cases`. A test that depends on state a fresh clone does not
have is not a test, it is a coincidence.

This builds a real database from the committed schema in a temporary directory
and points the application at it for the whole session, so every run starts from
the same known state on any machine.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "engine" / "db" / "schema.sql"


@pytest.fixture(scope="session", autouse=True)
def isolated_database() -> None:
    """Point MIZAN_DATABASE_URL at a temporary database built from schema.sql.

    Session-scoped and autouse: the application reads the environment variable
    when it resolves a connection, so this must be set before any test touches a
    route. The directory is kept for the session and removed by the operating
    system afterwards; nothing is written inside the repository.
    """
    tmp_dir = tempfile.mkdtemp(prefix="mizan-tests-")
    db_path = Path(tmp_dir) / "mizan.db"

    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.commit()

    previous = os.environ.get("MIZAN_DATABASE_URL")
    os.environ["MIZAN_DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

    yield

    if previous is None:
        os.environ.pop("MIZAN_DATABASE_URL", None)
    else:
        os.environ["MIZAN_DATABASE_URL"] = previous
