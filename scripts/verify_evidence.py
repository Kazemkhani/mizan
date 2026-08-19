#!/usr/bin/env python3
"""MIZAN evidence integrity audit script.

Walks the evidence table, recomputes every payload_hash from its stored
payload, verifies the hash chain for each evaluation, recomputes each
evaluation's bundle hash, and cross-checks against the certificate record.

Exit code 0: all checks pass. Status: CLEAN.
Exit code 1: one or more failures. Status: COMPROMISED.

AUDITOR runs this script at every wave gate. Wave 5 runs it from a clean
checkout. Make its output human-readable; do not print only a final verdict.

Usage:
    uv run python scripts/verify_evidence.py
    uv run python scripts/verify_evidence.py --db /path/to/mizan.db

What is verified per evidence row:
  - SHA-256(stored payload) == stored payload_hash.

What is verified per evaluation:
  - The hash chain is a valid single-linked list from a genesis row
    (chain_prev_hash = '') to a tail with no successor.
  - No row is unreachable (orphaned) from the chain.
  - SHA-256(sort(payload_hashes).join("")) == each evaluation's bundle hash
    in the certificates table (if a certificate exists).

What is NOT verified (and why):
  - The cryptographic signature on the certificate. The signing key is a
    stub in Wave 0; see docs/DECISIONS.md D-006.
  - Whether the triggers are still present. Run:
      sqlite3 data/mizan.db ".schema" | grep TRIGGER
    to confirm triggers have not been dropped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_DB = _REPO_ROOT / "data" / "mizan.db"


def sha256_text(text: str) -> str:
    """Return the hex-encoded SHA-256 digest of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bundle_hash(payload_hashes: list[str]) -> str:
    """Compute the evidence bundle hash for a certificate.

    SHA-256 of the lexicographically sorted payload_hashes concatenated.
    This matches the algorithm in mizan/engine/db/database.py.
    """
    combined = "".join(sorted(payload_hashes))
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def traverse_chain(rows: list[dict]) -> tuple[bool, str, list[dict]]:
    """Traverse the linked-list hash chain for one evaluation.

    Returns (ok, message, ordered_rows).
    ordered_rows is the chain in traversal order (genesis first) when ok is True.
    """
    if not rows:
        return True, "no rows", []

    genesis = [r for r in rows if r["chain_prev_hash"] == ""]
    if len(genesis) == 0:
        return False, "no genesis row (chain_prev_hash = '') found", []
    if len(genesis) > 1:
        ids = ", ".join(r["id"] for r in genesis)
        return False, f"multiple genesis rows: {ids}", []

    index_by_prev = {}
    for r in rows:
        prev = r["chain_prev_hash"]
        if prev in index_by_prev:
            return False, (
                f"forked chain: two rows both have chain_prev_hash = {prev[:12]}..."
            ), []
        index_by_prev[prev] = r

    ordered: list[dict] = []
    current = genesis[0]
    visited: set[str] = set()
    while True:
        h = current["payload_hash"]
        if h in visited:
            return False, f"cycle detected at payload_hash {h[:12]}...", []
        visited.add(h)
        ordered.append(current)
        nxt = index_by_prev.get(h)
        if nxt is None:
            break
        current = nxt

    if len(ordered) != len(rows):
        n_orphan = len(rows) - len(ordered)
        return False, f"{n_orphan} row(s) not reachable from chain genesis", []

    return True, f"{len(ordered)} rows, no gaps", ordered


def audit(db_path: Path) -> int:
    """Run the full audit. Returns 0 on clean, 1 on any failure."""
    if not db_path.exists():
        print(f"ERROR: database not found at {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    print("MIZAN Evidence Integrity Audit")
    print("=" * 60)
    print(f"Database : {db_path}")
    print()

    # Fetch all evidence rows.
    ev_rows = conn.execute("""
        SELECT id, evaluation_id, payload, payload_hash, chain_prev_hash
        FROM evidence
        ORDER BY evaluation_id, rowid
    """).fetchall()

    if not ev_rows:
        print("No evidence rows found. Nothing to audit.")
        conn.close()
        return 0

    # Group by evaluation.
    by_eval: dict[str, list[dict]] = {}
    for row in ev_rows:
        eid = row["evaluation_id"]
        by_eval.setdefault(eid, []).append(dict(row))

    # Fetch all certificates keyed by evaluation_id.
    certs = {
        r["evaluation_id"]: dict(r)
        for r in conn.execute(
            "SELECT evaluation_id, id, evidence_bundle_hash FROM certificates"
        ).fetchall()
    }

    total_rows = len(ev_rows)
    total_hash_failures = 0
    total_chain_failures = 0
    total_bundle_failures = 0

    print(f"Evidence rows : {total_rows} across {len(by_eval)} evaluation(s)")
    print()

    for eval_id, rows in sorted(by_eval.items()):
        print(f"Evaluation {eval_id}:")
        print(f"  Evidence rows : {len(rows)}")

        # 1. Payload hash verification.
        hash_fails: list[str] = []
        for r in rows:
            computed = sha256_text(r["payload"])
            if computed != r["payload_hash"]:
                hash_fails.append(
                    f"    FAIL row {r['id']}: "
                    f"stored={r['payload_hash'][:16]}... "
                    f"computed={computed[:16]}..."
                )
        if hash_fails:
            print(f"  Payload hash  : FAIL ({len(hash_fails)} mismatch(es))")
            for msg in hash_fails:
                print(msg)
            total_hash_failures += len(hash_fails)
        else:
            print(f"  Payload hash  : OK ({len(rows)}/{len(rows)} match)")

        # 2. Hash chain verification.
        chain_ok, chain_msg, ordered = traverse_chain(rows)
        if chain_ok:
            print(f"  Hash chain    : OK ({chain_msg})")
        else:
            print(f"  Hash chain    : BROKEN ({chain_msg})")
            total_chain_failures += 1

        # 3. Certificate bundle hash cross-check.
        cert = certs.get(eval_id)
        if cert is None:
            print("  Bundle hash   : no certificate (evaluation may still be running)")
        else:
            payload_hashes = [r["payload_hash"] for r in rows]
            computed_bundle = bundle_hash(payload_hashes)
            stored_bundle = cert["evidence_bundle_hash"]
            if computed_bundle == stored_bundle:
                print(f"  Bundle hash   : MATCH (cert {cert['id']})")
            else:
                print(
                    f"  Bundle hash   : MISMATCH (cert {cert['id']})\n"
                    f"    stored   = {stored_bundle[:32]}...\n"
                    f"    computed = {computed_bundle[:32]}..."
                )
                total_bundle_failures += 1

        print()

    # Check triggers are still present.
    trigger_names = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
    }
    expected_triggers = {
        "trg_evidence_insert_validate",
        "trg_evidence_no_update",
        "trg_evidence_no_delete",
        "trg_certificates_no_update",
        "trg_certificates_no_delete",
    }
    missing = expected_triggers - trigger_names
    if missing:
        print(f"WARNING: {len(missing)} trigger(s) are missing from the database:")
        for t in sorted(missing):
            print(f"  {t}")
        print(
            "  The immutability guarantees are not enforced at the database level."
        )
        print()

    conn.close()

    # Summary.
    total_failures = total_hash_failures + total_chain_failures + total_bundle_failures
    print("-" * 60)
    print("Summary")
    print(f"  Evaluations checked    : {len(by_eval)}")
    print(f"  Evidence rows checked  : {total_rows}")
    print(f"  Hash mismatches        : {total_hash_failures}")
    print(f"  Chain breaks           : {total_chain_failures}")
    print(f"  Bundle hash mismatches : {total_bundle_failures}")
    missing_count = len(missing) if missing else 0
    print(f"  Missing triggers       : {missing_count}")
    print()
    if total_failures == 0 and missing_count == 0:
        print("Status : CLEAN")
        return 0
    else:
        print("Status : COMPROMISED")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MIZAN evidence integrity audit")
    parser.add_argument(
        "--db",
        default=str(_DEFAULT_DB),
        help=f"Path to the SQLite database (default: {_DEFAULT_DB})",
    )
    args = parser.parse_args()
    sys.exit(audit(Path(args.db)))
