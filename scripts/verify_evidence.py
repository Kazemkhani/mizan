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
  - The adjudication columns (passed, score, suite_id, control_id) agree with
    the corresponding fields in the payload. This check is independent of the
    hash: it detects the attack where a row carries a valid hash over a payload
    that contradicts the column values from which the certificate is computed.
    A trigger added in schema v0.3.0 blocks this attack at insert time; the
    verify script detects it on rows written by an older schema version or by
    a direct database write that bypassed the trigger.

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

    # Fetch all evidence rows, including the adjudication columns whose
    # consistency with the payload is checked independently of the hash.
    ev_rows = conn.execute("""
        SELECT id, evaluation_id, payload, payload_hash, chain_prev_hash,
               score, passed, suite_id, control_id
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
    total_column_failures = 0
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

        # 1b. Column-payload consistency verification.
        #
        # This check is independent of the hash. It detects the L1 attack:
        # a row whose payload is honestly hashed but whose adjudication columns
        # (passed, score, suite_id, control_id) contradict the payload values
        # from which the certificate is computed. The hash check above reports
        # CLEAN in that scenario; only this check catches the contradiction.
        #
        # A trigger in schema v0.3.0 blocks this at insert time. This check
        # catches rows written under an older schema or by a direct database
        # write that bypassed the trigger.
        col_fails: list[str] = []
        for r in rows:
            try:
                payload_data = json.loads(r["payload"])
            except (json.JSONDecodeError, TypeError):
                # Payload is not valid JSON. The hash check above will report
                # a mismatch (the stored hash cannot match the garbled payload).
                # Do not double-report here; just note it.
                col_fails.append(
                    f"    FAIL row {r['id']}: payload is not valid JSON "
                    f"(column-payload consistency cannot be checked)"
                )
                continue

            # Check passed.
            payload_passed = payload_data.get("passed")
            if payload_passed is None:
                col_fails.append(
                    f"    FAIL row {r['id']}: "
                    f"payload missing required 'passed' field"
                )
            elif int(bool(payload_passed)) != r["passed"]:
                col_fails.append(
                    f"    FAIL row {r['id']}: "
                    f"passed column={r['passed']} contradicts "
                    f"payload.passed={payload_passed!r}"
                )

            # Check score.
            payload_score = payload_data.get("score")
            if payload_score is None:
                col_fails.append(
                    f"    FAIL row {r['id']}: "
                    f"payload missing required 'score' field"
                )
            elif abs(float(payload_score) - float(r["score"])) > 1e-9:
                col_fails.append(
                    f"    FAIL row {r['id']}: "
                    f"score column={r['score']} contradicts "
                    f"payload.score={payload_score!r}"
                )

            # Check suite_id (when the payload declares it).
            payload_suite_id = payload_data.get("suite_id")
            if payload_suite_id is not None and payload_suite_id != r["suite_id"]:
                col_fails.append(
                    f"    FAIL row {r['id']}: "
                    f"suite_id column={r['suite_id']!r} contradicts "
                    f"payload.suite_id={payload_suite_id!r}"
                )

            # Check control_id (when the payload declares it).
            payload_control_id = payload_data.get("control_id")
            if payload_control_id is not None and payload_control_id != r["control_id"]:
                col_fails.append(
                    f"    FAIL row {r['id']}: "
                    f"control_id column={r['control_id']!r} contradicts "
                    f"payload.control_id={payload_control_id!r}"
                )

        if col_fails:
            print(
                f"  Column-payload: COMPROMISED ({len(col_fails)} "
                f"contradiction(s); certificate verdict is not trustworthy)"
            )
            for msg in col_fails:
                print(msg)
            total_column_failures += len(col_fails)
        else:
            print(f"  Column-payload: OK ({len(rows)}/{len(rows)} consistent)")

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
    total_failures = (
        total_hash_failures
        + total_column_failures
        + total_chain_failures
        + total_bundle_failures
    )
    print("-" * 60)
    print("Summary")
    print(f"  Evaluations checked         : {len(by_eval)}")
    print(f"  Evidence rows checked       : {total_rows}")
    print(f"  Hash mismatches             : {total_hash_failures}")
    print(f"  Column-payload contradictions: {total_column_failures}")
    print(f"  Chain breaks                : {total_chain_failures}")
    print(f"  Bundle hash mismatches      : {total_bundle_failures}")
    missing_count = len(missing) if missing else 0
    print(f"  Missing triggers            : {missing_count}")
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
