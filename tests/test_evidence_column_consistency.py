"""Attacker tests for L1: adjudication columns are not bound to the evidence hash.

The defect: the SHA-256 hash covers the `payload` column only. The `score`,
`passed`, `control_id`, and `suite_id` columns are outside it, yet those
columns are what the certificate is computed from. A row can therefore carry
a validly-hashed payload while its columns contradict it. Every integrity
check in the system reports CLEAN.

These tests are written from the attacker's perspective, not the defender's.
They describe three distinct attack surfaces and one baseline to confirm the
fix does not block legitimate writes.

METHODOLOGY
-----------
Each test connects to a fresh SQLite database with the full schema applied and
uses the stdlib sqlite3 module directly, so it exercises the triggers without
any application-layer intermediary. The attack tests must:

  1. FAIL before the fix is applied (meaning: the attack INSERT succeeds when
     it should be blocked).
  2. PASS after the fix is applied (meaning: the attack INSERT is blocked by
     the trigger and raises sqlite3.IntegrityError).

Before committing the fix, these three attack tests were run against the
unpatched schema and all three raised AssertionError or the wrong exception,
confirming the vulnerability was live. The fix adds column-payload consistency
checks to `trg_evidence_insert_validate`.

ATTACKS COVERED
---------------
  Attack A: INSERT whose columns contradict the payload.
    payload.passed = False, column passed = 1. Hash is valid (computed from
    the honest payload). The certificate uses the column; it would assert a
    pass on a probe that actually failed. verify_evidence.py reported CLEAN.

  Attack B: INSERT whose payload omits the adjudication fields entirely.
    A payload without 'passed' or 'score' cannot be checked for consistency.
    Any column value would appear consistent because there is nothing to
    compare against. The trigger must reject an incomplete payload.

  Attack C: INSERT where score column contradicts payload.score.
    payload.score = 0.0, column score = 1.0. Hash is valid. The certificate
    uses the column score; it would report a high-scoring probe that actually
    scored zero.

Baseline: a legitimate INSERT where every column exactly matches the payload
must succeed with no error.

British English throughout.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "engine" / "db" / "schema.sql"

_NOW = "2026-01-01T00:00:00+00:00"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_mizan.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    return db_path


def _open(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _seed(conn: sqlite3.Connection) -> None:
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


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _payload_str(data: dict) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Attack A: columns contradict the payload (the primary L1 vector)
# ---------------------------------------------------------------------------

def test_attack_a_passed_column_contradicts_payload(tmp_path):
    """ATTACK A: INSERT where payload.passed=False but column passed=1.

    This is the exact attack the external auditor demonstrated. The payload
    honestly records a probe failure. The column is flipped to 1 (pass).
    The SHA-256 hash is valid because it was computed from the honest payload.
    Without the fix, verify_evidence.py reports CLEAN.

    After the fix, the trigger must detect that 1 != json_extract(payload, '$.passed')
    and raise IntegrityError.
    """
    db = _fresh_db(tmp_path)
    payload = _payload_str({
        "probe_id": "p-attack",
        "passed": False,   # honest: the probe failed
        "score": 0.0,
        "suite_id": "suite-t",
        "control_id": "ctrl-t",
    })
    valid_hash = _sha256(payload)

    with _open(db) as conn:
        _seed(conn)
        with pytest.raises(sqlite3.IntegrityError, match="contradicts"):
            conn.execute("""
                INSERT INTO evidence
                    (id, evaluation_id, suite_id, control_id, probe_id,
                     payload, payload_hash, chain_prev_hash, score, passed, collected_at)
                VALUES (?, 'eval-t', 'suite-t', 'ctrl-t', 'p-attack', ?, ?, '', 0.0, 1, ?)
            """, (
                "ev-attack-a",
                payload,
                valid_hash,
                # passed = 1 contradicts payload.passed = false
                _NOW,
            ))


# ---------------------------------------------------------------------------
# Attack B: payload omits the adjudication fields entirely
# ---------------------------------------------------------------------------

def test_attack_b_payload_omits_passed_field(tmp_path):
    """ATTACK B: INSERT where the payload has no 'passed' key at all.

    A payload without 'passed' cannot be checked for consistency with the
    column. An attacker who controls the insert path could supply an arbitrary
    'passed' column value with no contradicting evidence in the payload. The
    trigger must reject a payload that omits this required adjudication field.

    After the fix, the trigger raises IntegrityError indicating the field is
    required.
    """
    db = _fresh_db(tmp_path)
    # Payload deliberately omits 'passed' and 'score'.
    payload = _payload_str({
        "probe_id": "p-omit",
        "suite_id": "suite-t",
        "control_id": "ctrl-t",
        "response": "some text",
    })
    valid_hash = _sha256(payload)

    with _open(db) as conn:
        _seed(conn)
        with pytest.raises(sqlite3.IntegrityError, match="must contain"):
            conn.execute("""
                INSERT INTO evidence
                    (id, evaluation_id, suite_id, control_id, probe_id,
                     payload, payload_hash, chain_prev_hash, score, passed, collected_at)
                VALUES (?, 'eval-t', 'suite-t', 'ctrl-t', 'p-omit', ?, ?, '', 0.0, 0, ?)
            """, ("ev-attack-b", payload, valid_hash, _NOW))


# ---------------------------------------------------------------------------
# Attack C: score column contradicts payload.score
# ---------------------------------------------------------------------------

def test_attack_c_score_column_contradicts_payload(tmp_path):
    """ATTACK C: INSERT where payload.score=0.0 but column score=1.0.

    The payload records a low score. The column is set to 1.0. The certificate
    reports the column value as the model's score on this control. A certificate
    that shows score=1.0 while the raw evidence records 0.0 is fraudulent.

    After the fix, the trigger must detect that 1.0 != json_extract(payload, '$.score')
    and raise IntegrityError.
    """
    db = _fresh_db(tmp_path)
    payload = _payload_str({
        "probe_id": "p-score",
        "passed": False,
        "score": 0.0,      # honest: low score
        "suite_id": "suite-t",
        "control_id": "ctrl-t",
    })
    valid_hash = _sha256(payload)

    with _open(db) as conn:
        _seed(conn)
        with pytest.raises(sqlite3.IntegrityError, match="contradicts"):
            conn.execute("""
                INSERT INTO evidence
                    (id, evaluation_id, suite_id, control_id, probe_id,
                     payload, payload_hash, chain_prev_hash, score, passed, collected_at)
                VALUES (?, 'eval-t', 'suite-t', 'ctrl-t', 'p-score', ?, ?, '', 1.0, 0, ?)
            """, (
                "ev-attack-c",
                payload,
                valid_hash,
                # score = 1.0 contradicts payload.score = 0.0
                _NOW,
            ))


# ---------------------------------------------------------------------------
# Baseline: a legitimate, fully-consistent INSERT must succeed
# ---------------------------------------------------------------------------

def test_baseline_consistent_insert_succeeds(tmp_path):
    """BASELINE: an INSERT where every column exactly matches the payload succeeds.

    This confirms the fix does not break legitimate writes. The columns are a
    correct projection of the payload and the hash is valid.
    """
    db = _fresh_db(tmp_path)
    payload = _payload_str({
        "probe_id": "p-legit",
        "passed": True,
        "score": 0.85,
        "suite_id": "suite-t",
        "control_id": "ctrl-t",
        "response": "The answer is correct.",
    })
    valid_hash = _sha256(payload)

    with _open(db) as conn:
        _seed(conn)
        conn.execute("""
            INSERT INTO evidence
                (id, evaluation_id, suite_id, control_id, probe_id,
                 payload, payload_hash, chain_prev_hash, score, passed, collected_at)
            VALUES (?, 'eval-t', 'suite-t', 'ctrl-t', 'p-legit', ?, ?, '', 0.85, 1, ?)
        """, ("ev-legit", payload, valid_hash, _NOW))
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]

    assert count == 1, "legitimate evidence row was not inserted"
