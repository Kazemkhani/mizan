"""Evidence retrieval routes.

GET /api/v1/evidence/{hash}            -- retrieve one evidence record by payload hash
GET /api/v1/evidence                   -- list evidence for an evaluation

Evidence records are append-only and content-addressed. Every record carries
a SHA-256 hash of its payload; a caller can re-hash the returned payload and
compare to payload_hash to verify the record has not been altered.

Handlers return fixture data in Wave 0. Wave 1 (HARNESS) wires real DB calls.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from mizan.api.schemas import EvidenceRow

router = APIRouter(prefix="/evidence", tags=["evidence"])

# Wave 0 fixture store. Wave 1 replaces with DB calls.
_FIXTURE_STORE: dict[str, dict] = {}


def _register_evidence(record: dict) -> None:
    """Register an evidence record in the Wave 0 fixture store.

    Called by the evaluation harness (Wave 1) when it writes evidence.
    In Wave 1 this function is removed and DB writes happen directly.
    """
    _FIXTURE_STORE[record["payload_hash"]] = record


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
    record = _FIXTURE_STORE.get(payload_hash)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No evidence record found for hash '{payload_hash}'.",
        )
    return EvidenceRow(**record)


@router.get(
    "",
    response_model=list[EvidenceRow],
    summary="List evidence records for an evaluation",
)
async def list_evidence(
    evaluation_id: str = Query(..., description="Evaluation ID to filter evidence by"),
) -> list[EvidenceRow]:
    """Return all evidence records for the given evaluation, sorted by collection time."""
    records = [
        r for r in _FIXTURE_STORE.values() if r["evaluation_id"] == evaluation_id
    ]
    records.sort(key=lambda r: r["collected_at"])
    return [EvidenceRow(**r) for r in records]
