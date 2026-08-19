"""Certificate retrieval routes.

GET /api/v1/certificates/{id}     -- retrieve a certificate by ID
GET /api/v1/certificates          -- list certificates (optional model_id filter)

A certificate is issued by the evaluation engine on completion and references
an evidence_bundle_hash that allows independent verification outside the
database. Certificates are read-only after issuance; they are never updated.

Handlers return fixture data in Wave 0. Wave 3 (GOVERNANCE + RASHID) wires
the PDF renderer and the real certificate data.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from mizan.api.schemas import CertificateOut

router = APIRouter(prefix="/certificates", tags=["certificates"])

_FIXTURE_STORE: dict[str, dict] = {}


def _register_certificate(record: dict) -> None:
    """Register a certificate in the Wave 0 fixture store.

    In Wave 1+ this is replaced by the evaluation engine writing directly
    to the database on adjudication completion.
    """
    _FIXTURE_STORE[record["id"]] = record


@router.get(
    "/{certificate_id}",
    response_model=CertificateOut,
    summary="Retrieve a certificate",
    description=(
        "Return a MIZAN compliance certificate. The evidence_bundle_hash "
        "field allows independent verification: retrieve all evidence records "
        "for the evaluation, sort their payload_hash values lexicographically, "
        "concatenate them, and compute SHA-256 to reproduce the bundle hash."
    ),
)
async def get_certificate(certificate_id: str) -> CertificateOut:
    """Return the full certificate record for the given certificate ID."""
    record = _FIXTURE_STORE.get(certificate_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Certificate '{certificate_id}' not found.",
        )
    return CertificateOut(**record)


@router.get(
    "",
    response_model=list[CertificateOut],
    summary="List certificates",
)
async def list_certificates(
    model_id: str | None = Query(default=None, description="Filter by model ID"),
) -> list[CertificateOut]:
    """Return all certificates, optionally filtered by model ID."""
    records = _FIXTURE_STORE.values()
    if model_id:
        records = [r for r in records if r["model_id"] == model_id]
    return [CertificateOut(**r) for r in records]
