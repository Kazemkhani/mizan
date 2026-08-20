"""Tests proving database-level immutability enforcement on evidence and certificates.

Each test connects directly to a fresh SQLite database with the full schema
applied. Tests use the stdlib sqlite3 module so they exercise the triggers
without any application-layer intermediary. This is deliberate: a trigger
that only stops application code stops nothing when someone queries the
database directly.

The three attacks documented in the F0-01 audit finding must each raise
sqlite3.IntegrityError. That error message must contain the expected
keyword so the failure reason is unambiguous in CI output.

Acceptance criteria:
  - Legitimate inserts succeed (trigger is not simply broken).
  - Attack 1 (rewrite passed/score) raises and aborts.
  - Attack 2 (rewrite payload and hash) raises and aborts.
  - Attack 3 (delete evidence) raises and aborts.
  - Invalid payload_hash length raises and aborts.
  - Certificate DELETE raises and aborts.
  - Certificate verdict UPDATE raises and aborts.
  - Certificate pdf_path UPDATE succeeds (allowed post-issuance field).
  - Hash chain genesis rules are enforced.
  - Hash chain linking rules are enforced.
  - append_evidence() computes payload_hash itself; caller cannot supply a hash.
  - Concurrent fork attempt (two rows with same chain_prev_hash) is blocked
    by the UNIQUE index on (evaluation_id, chain_prev_hash).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from mizan.engine.db.database import (
    _append_evidence_sync,
    canonical_payload,
    sha256_of,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "engine" / "db" / "schema.sql"

_NOW = "2026-01-01T00:00:00+00:00"
_HASH_A = "a" * 64  # valid 64-char hex string
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64

# _PAYLOAD must include the adjudication fields (passed, score, suite_id,
# control_id) so that the schema v0.3.0 column-payload consistency trigger
# passes when these tests insert with the default column values
# (score=0.0, passed=0, suite_id='suite-t', control_id='ctrl-t').
_PAYLOAD = json.dumps(
    {
        "control_id": "ctrl-t",
        "passed": False,
        "probe_id": "p1",
        "score": 0.0,
        "suite_id": "suite-t",
    },
    sort_keys=True,
)
_PAYLOAD_HASH = hashlib.sha256(_PAYLOAD.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    """Fresh SQLite database with the full schema and triggers applied."""
    db_path = tmp_path / "test_mizan.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    # Enable foreign key enforcement for this connection.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    return db_path


def _open(db_path) -> sqlite3.Connection:
    """Open a connection with foreign keys enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _seed(conn: sqlite3.Connection) -> None:
    """Insert the minimum rows required by foreign key constraints."""
    conn.execute("""
        INSERT OR IGNORE INTO use_cases
            (id, name_en, name_ar, description_en, description_ar,
             use_case_class, confidence_threshold, created_at)
        VALUES ('uc-t', 'Test UC', 'اختبار', 'Desc', 'وصف', 'test', 0.95, ?)
    """, (_NOW,))
    conn.execute("""
        INSERT OR IGNORE INTO models
            (id, name_en, name_ar, provider, version, model_card, submitted_at, updated_at)
        VALUES ('mdl-t', 'Test', 'اختبار', 'Prov', '1.0', '{}', ?, ?)
    """, (_NOW, _NOW))
    conn.execute("""
        INSERT OR IGNORE INTO controls
            (id, use_case_id, name_en, name_ar, description_en, description_ar,
             framework_clause, suite_id, created_at)
        VALUES ('ctrl-t', 'uc-t', 'C', 'ض', 'Desc', 'وصف', 'Principle 1', 'suite-t', ?)
    """, (_NOW,))
    conn.execute("""
        INSERT OR IGNORE INTO evaluations
            (id, model_id, use_case_id, started_at)
        VALUES ('eval-t', 'mdl-t', 'uc-t', ?)
    """, (_NOW,))
    conn.commit()


def _insert_evidence(
    conn: sqlite3.Connection,
    ev_id: str = "ev-001",
    payload_hash: str = _HASH_A,
    chain_prev_hash: str = "",
    payload: str = _PAYLOAD,
    score: float = 0.0,
    passed: int = 0,
) -> None:
    conn.execute("""
        INSERT INTO evidence
            (id, evaluation_id, suite_id, control_id, probe_id,
             payload, payload_hash, chain_prev_hash, score, passed, collected_at)
        VALUES (?, 'eval-t', 'suite-t', 'ctrl-t', 'p1', ?, ?, ?, ?, ?, ?)
    """, (ev_id, payload, payload_hash, chain_prev_hash, score, passed, _NOW))
    conn.commit()


def _insert_certificate(
    conn: sqlite3.Connection,
    cert_id: str = "cert-001",
    eval_id: str = "eval-cert",
    verdict: str = "certified",
) -> None:
    conn.execute("""
        INSERT OR IGNORE INTO evaluations
            (id, model_id, use_case_id, status, verdict, started_at, completed_at)
        VALUES (?, 'mdl-t', 'uc-t', 'completed', ?, ?, ?)
    """, (eval_id, verdict, _NOW, _NOW))
    conn.execute("""
        INSERT INTO certificates
            (id, evaluation_id, model_id, use_case_id, verdict,
             evidence_bundle_hash, issued_at)
        VALUES (?, ?, 'mdl-t', 'uc-t', ?, ?, ?)
    """, (cert_id, eval_id, verdict, _HASH_C, _NOW))
    conn.commit()


# ---------------------------------------------------------------------------
# Baseline: legitimate operations must succeed
# ---------------------------------------------------------------------------

def test_legitimate_evidence_insert_succeeds(db):
    """A valid evidence row with a correctly formed hash can be inserted."""
    with _open(db) as conn:
        _seed(conn)
        _insert_evidence(conn)
        count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    assert count == 1


def test_chained_evidence_inserts_succeed(db):
    """Two evidence rows linked by chain_prev_hash can both be inserted."""
    with _open(db) as conn:
        _seed(conn)
        _insert_evidence(conn, ev_id="ev-001", payload_hash=_HASH_A, chain_prev_hash="")
        _insert_evidence(conn, ev_id="ev-002", payload_hash=_HASH_B, chain_prev_hash=_HASH_A)
        count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    assert count == 2


# ---------------------------------------------------------------------------
# F0-01 Attack 1: rewrite verdict fields on an evidence row
# ---------------------------------------------------------------------------

def test_attack_1_update_passed_blocked(db):
    """ATTACK 1: setting passed=1 score=1.0 on a failing probe must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_evidence(conn, passed=0, score=0.0)
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(
                "UPDATE evidence SET passed = 1, score = 1.0 WHERE id = 'ev-001'"
            )


# ---------------------------------------------------------------------------
# F0-01 Attack 2: rewrite payload while also rewriting the stored hash
# ---------------------------------------------------------------------------

def test_attack_2_update_payload_and_hash_blocked(db):
    """ATTACK 2: rewriting payload and payload_hash together must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_evidence(conn)
    tampered_payload = json.dumps({"probe_id": "p1", "passed": True}, sort_keys=True)
    tampered_hash = hashlib.sha256(tampered_payload.encode()).hexdigest()
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(
                "UPDATE evidence SET payload = ?, payload_hash = ? WHERE id = 'ev-001'",
                (tampered_payload, tampered_hash),
            )


# ---------------------------------------------------------------------------
# F0-01 Attack 3: delete an evidence row
# ---------------------------------------------------------------------------

def test_attack_3_delete_evidence_blocked(db):
    """ATTACK 3: deleting an evidence row must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_evidence(conn)
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute("DELETE FROM evidence WHERE id = 'ev-001'")


# ---------------------------------------------------------------------------
# payload_hash format validation
# ---------------------------------------------------------------------------

def test_payload_hash_too_short_rejected(db):
    """An evidence row with a payload_hash shorter than 64 characters must be rejected."""
    with _open(db) as conn:
        _seed(conn)
        with pytest.raises(sqlite3.IntegrityError, match="payload_hash must be 64 characters"):
            _insert_evidence(conn, payload_hash="abc123")


def test_payload_hash_too_long_rejected(db):
    """An evidence row with a payload_hash longer than 64 characters must be rejected."""
    with _open(db) as conn:
        _seed(conn)
        with pytest.raises(sqlite3.IntegrityError, match="payload_hash must be 64 characters"):
            _insert_evidence(conn, payload_hash="a" * 65)


# ---------------------------------------------------------------------------
# Hash chain enforcement
# ---------------------------------------------------------------------------

def test_second_genesis_row_blocked(db):
    """A second genesis row (chain_prev_hash = '') for the same evaluation must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_evidence(conn, ev_id="ev-001", payload_hash=_HASH_A, chain_prev_hash="")
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="chain_prev_hash may be empty only"):
            _insert_evidence(conn, ev_id="ev-002", payload_hash=_HASH_B, chain_prev_hash="")


def test_orphan_chain_prev_hash_blocked(db):
    """A non-genesis row whose chain_prev_hash references no existing hash must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_evidence(conn, ev_id="ev-001", payload_hash=_HASH_A, chain_prev_hash="")
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="chain_prev_hash does not reference"):
            _insert_evidence(
                conn, ev_id="ev-002", payload_hash=_HASH_B,
                chain_prev_hash="f" * 64,  # no row with this hash exists
            )


# ---------------------------------------------------------------------------
# Certificate immutability
# ---------------------------------------------------------------------------

def test_certificate_delete_blocked(db):
    """Deleting a certificate must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_certificate(conn)
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="deleted"):
            conn.execute("DELETE FROM certificates WHERE id = 'cert-001'")


def test_certificate_verdict_immutable(db):
    """Changing the verdict on an issued certificate must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_certificate(conn, cert_id="cert-v", eval_id="eval-v", verdict="certified")
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE certificates SET verdict = 'rejected' WHERE id = 'cert-v'"
            )


def test_certificate_evidence_bundle_hash_immutable(db):
    """Changing the evidence_bundle_hash on an issued certificate must abort."""
    with _open(db) as conn:
        _seed(conn)
        _insert_certificate(conn, cert_id="cert-h", eval_id="eval-h")
    with _open(db) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE certificates SET evidence_bundle_hash = ? WHERE id = 'cert-h'",
                (_HASH_D,),
            )


def test_certificate_pdf_path_update_allowed(db):
    """Setting pdf_path after issuance must succeed (permitted post-issuance field)."""
    with _open(db) as conn:
        _seed(conn)
        _insert_certificate(conn, cert_id="cert-p", eval_id="eval-p")
    with _open(db) as conn:
        conn.execute(
            "UPDATE certificates SET pdf_path = 'docs/certs/cert-p.pdf' WHERE id = 'cert-p'"
        )
        conn.commit()
        pdf = conn.execute(
            "SELECT pdf_path FROM certificates WHERE id = 'cert-p'"
        ).fetchone()[0]
    assert pdf == "docs/certs/cert-p.pdf"


def test_certificate_signature_update_allowed(db):
    """Setting signature after issuance must succeed (wired in Wave 3)."""
    with _open(db) as conn:
        _seed(conn)
        _insert_certificate(conn, cert_id="cert-s", eval_id="eval-s")
    with _open(db) as conn:
        conn.execute(
            "UPDATE certificates SET signature = 'hmac-stub-value' WHERE id = 'cert-s'"
        )
        conn.commit()
        sig = conn.execute(
            "SELECT signature FROM certificates WHERE id = 'cert-s'"
        ).fetchone()[0]
    assert sig == "hmac-stub-value"


# ---------------------------------------------------------------------------
# append_evidence() write path: forged hash prevention
# ---------------------------------------------------------------------------

def test_append_evidence_computes_hash_itself(db):
    """append_evidence() must compute payload_hash from the payload; the caller
    supplies no hash and cannot forge one.

    We call _append_evidence_sync (the synchronous core) directly with a
    payload dict and then read the stored row back. The stored payload_hash
    must equal sha256_of(canonical_payload(payload_dict)), which is the
    value the function computed internally. The caller had no opportunity
    to supply a different hash.
    """
    # Include all adjudication fields so the schema v0.3.0 trigger passes.
    # The trigger verifies that columns agree with the payload; the payload
    # must therefore contain passed, score, suite_id, and control_id.
    payload_dict = {
        "probe_id": "p-forge",
        "result": "fail",
        "score": 0.0,
        "passed": False,
        "suite_id": "suite-t",
        "control_id": "ctrl-t",
    }
    expected_text = canonical_payload(payload_dict)
    expected_hash = sha256_of(expected_text)

    with _open(db) as conn:
        _seed(conn)

    _append_evidence_sync(
        str(db),
        ev_id="ev-forge",
        evaluation_id="eval-t",
        suite_id="suite-t",
        control_id="ctrl-t",
        probe_id="p-forge",
        payload=payload_dict,
        score=0.0,
        passed=0,
        collected_at=_NOW,
    )

    with _open(db) as conn:
        row = conn.execute(
            "SELECT payload, payload_hash, chain_prev_hash FROM evidence WHERE id = 'ev-forge'"
        ).fetchone()

    assert row is not None, "evidence row was not inserted"
    stored_payload, stored_hash, chain_prev = row

    # The stored payload must be the canonical serialisation.
    assert stored_payload == expected_text, (
        "stored payload does not match canonical_payload() output"
    )
    # The stored hash must equal sha256 of the stored payload.
    assert stored_hash == expected_hash, (
        "stored payload_hash does not equal sha256_of(canonical_payload(payload_dict))"
    )
    # verify_evidence.py recomputes sha256(stored_payload) and compares;
    # confirm the round-trip is consistent.
    assert sha256_of(stored_payload) == stored_hash, (
        "sha256_of(stored_payload) != stored_hash: verify script would report COMPROMISED"
    )
    # Genesis row: chain_prev_hash must be empty string.
    assert chain_prev == "", "first row for evaluation must be a genesis row"


# ---------------------------------------------------------------------------
# Concurrent fork prevention via UNIQUE index on (evaluation_id, chain_prev_hash)
# ---------------------------------------------------------------------------

def test_concurrent_fork_blocked_by_unique_index(db):
    """Two rows claiming the same chain_prev_hash in the same evaluation must be
    rejected by the UNIQUE index on (evaluation_id, chain_prev_hash).

    This is the database-level guard against concurrent-append forks. When two
    append_evidence() callers race and both read the same tail hash, only the
    first INSERT succeeds. The second raises sqlite3.IntegrityError with
    'UNIQUE constraint failed'. append_evidence() catches that specific error
    and retries with a fresh tail-hash read.
    """
    with _open(db) as conn:
        _seed(conn)
        # Row 1: genesis.
        _insert_evidence(conn, ev_id="ev-fork-1", payload_hash=_HASH_A, chain_prev_hash="")
        # Row 2: first successor, chain_prev_hash = _HASH_A.
        _insert_evidence(conn, ev_id="ev-fork-2", payload_hash=_HASH_B, chain_prev_hash=_HASH_A)

    with _open(db) as conn:
        # Simulate a second caller that also read _HASH_A as the tail (a race).
        # It tries to insert a third row with chain_prev_hash = _HASH_A.
        # This would fork the chain: both ev-fork-2 and this row would claim
        # chain_prev_hash = _HASH_A. The UNIQUE index must reject it.
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            _insert_evidence(
                conn, ev_id="ev-fork-3", payload_hash=_HASH_C, chain_prev_hash=_HASH_A
            )

    # Confirm the database is still intact: only two evidence rows exist.
    with _open(db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    assert count == 2, "fork attempt must not have inserted a third row"
