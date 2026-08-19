#!/usr/bin/env python3
"""MIZAN database reset script.

Drops and recreates the database, then runs the seeder.
Use this to return to a clean demo state between rehearsals.

Usage:
    uv run python scripts/reset.py          # reset and seed
    uv run python scripts/reset.py --no-seed  # reset only

WARNING: this drops all data in the SQLite file. It does not drop a
Postgres database; for Postgres, run the appropriate DROP/CREATE
commands manually then execute this script.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from mizan.engine.db.database import _DATABASE_URL, _DEFAULT_DB_PATH, engine, init_db


async def reset(seed: bool = True) -> None:
    """Drop all tables (SQLite: delete the file) then reinitialise."""

    if "sqlite" in _DATABASE_URL:
        db_path = _DEFAULT_DB_PATH
        if db_path.exists():
            db_path.unlink()
            print(f"Deleted {db_path}")
        else:
            print(f"No database file found at {db_path}; creating fresh.")
    else:
        # For Postgres, drop and recreate tables via DDL.
        # This is a placeholder; the actual Postgres reset would use
        # DROP TABLE IF EXISTS ... CASCADE for each table.
        # SOVEREIGN-TODO: implement Postgres reset path in Wave 3.
        print("Non-SQLite database detected. Only table re-initialisation is performed.")
        print("For Postgres, drop tables manually before running this script.")

    await init_db()
    print("Database initialised.")

    if seed:
        from scripts.seed import seed as run_seed
        await run_seed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset the MIZAN database.")
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Reinitialise the schema without seeding demo data.",
    )
    args = parser.parse_args()
    asyncio.run(reset(seed=not args.no_seed))
