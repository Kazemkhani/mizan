"""Evidence retrieval routes.

GET /api/v1/evidence?evaluation_id=...   -- list evidence for an evaluation
GET /api/v1/evidence/{hash}              -- retrieve one record by payload hash

Evidence records are append-only and content-addressed. Every record carries
a SHA-256 hash of its payload; a caller can re-hash the returned payload and
compare it to payload_hash to verify the record has not been altered.

Reads go to the evidence table, which is where append_evidence() writes. The
interface uses the list endpoint to open the exact probe and response behind
a control decision, which is only possible because the payload is stored
whole rather than summarised.

British English throughout.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from mizan.api import store
from mizan.api.schemas import EvidenceRow

router = APIRouter(prefix="/evidence", tags=["evidence"])


def _to_row(record: dict[str, Any]) -> EvidenceRow:
    try:
        payload = json.loads(record.get("payload") or "{}")
    except (json.JSONDecodeError, TypeError):
        payload = {}
    return EvidenceRow(
        id=record["id"],
        evaluation_id=record["evaluation_id"],
        suite_id=record["suite_id"],
        control_id=record["control_id"],
        probe_id=record["probe_id"],
        payload=payload,
        payload_hash=record["payload_hash"],
        score=record["score"],
        passed=bool(record["passed"]),
        collected_at=record["collected_at"],
    )


@router.get(
    "",
    response_model=list[EvidenceRow],
    summary="List evidence records for an evaluation",
)
async def list_evidence(
    evaluation_id: str = Query(..., description="Evaluation ID to filter evidence by"),
    control_id: str | None = Query(default=None, description="Filter to one control"),
    passed: bool | None = Query(default=None, description="Filter by probe outcome"),
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[EvidenceRow]:
    """Return evidence records for the evaluation, oldest first."""
    sql = "SELECT * FROM evidence WHERE evaluation_id = ?"
    params: list[Any] = [evaluation_id]
    if control_id:
        sql += " AND control_id = ?"
        params.append(control_id)
    if passed is not None:
        sql += " AND passed = ?"
        params.append(1 if passed else 0)
    sql += " ORDER BY collected_at ASC, rowid ASC LIMIT ?"
    params.append(limit)

    return [_to_row(r) for r in store.query(sql, tuple(params))]


@router.get(
    "/{payload_hash}",
    response_model=EvidenceRow,
    summary="Retrieve an evidence record by its payload hash",
    description=(
        "Look up a single evidence record by its SHA-256 content hash. "
        "The caller may verify integrity by computing SHA-256 of the "
        "returned payload and comparing it to payload_hash."
    ),
)
async def get_evidence_by_hash(payload_hash: str) -> EvidenceRow:
    """Return the evidence record identified by the given SHA-256 hex digest."""
    record = store.query_one(
        "SELECT * FROM evidence WHERE payload_hash = ?", (payload_hash,)
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No evidence record found for hash '{payload_hash}'.",
        )
    return _to_row(record)
