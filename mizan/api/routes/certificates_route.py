"""Certificate retrieval routes.

GET /api/v1/certificates                      -- list certificates
GET /api/v1/certificates/{id}                 -- retrieve a certificate by id
GET /api/v1/certificates/by-evaluation/{id}   -- retrieve the certificate an
                                                 evaluation issued

A certificate is issued by mizan.api.certificate when an evaluation reaches a
verdict, and references an evidence_bundle_hash that allows independent
verification outside the database. Certificates are read-only after issuance;
the table's triggers enforce that, and nothing here writes.

British English throughout.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from mizan.api import store
from mizan.api.certificate import _row_to_record
from mizan.api.schemas import CertificateOut

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get(
    "",
    response_model=list[CertificateOut],
    summary="List certificates",
)
async def list_certificates(
    model_id: str | None = Query(default=None, description="Filter by model ID"),
) -> list[CertificateOut]:
    """Return all certificates, most recently issued first."""
    if model_id:
        rows = store.query(
            "SELECT * FROM certificates WHERE model_id = ? ORDER BY issued_at DESC",
            (model_id,),
        )
    else:
        rows = store.query("SELECT * FROM certificates ORDER BY issued_at DESC")
    return [CertificateOut(**_row_to_record(r)) for r in rows]


@router.get(
    "/by-evaluation/{evaluation_id}",
    response_model=CertificateOut,
    summary="Retrieve the certificate issued by an evaluation",
)
async def get_certificate_for_evaluation(evaluation_id: str) -> CertificateOut:
    """Return the certificate an evaluation issued, if it reached a verdict."""
    row = store.query_one(
        "SELECT * FROM certificates WHERE evaluation_id = ?", (evaluation_id,)
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation '{evaluation_id}' has issued no certificate.",
        )
    return CertificateOut(**_row_to_record(row))


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
    row = store.query_one("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Certificate '{certificate_id}' not found.",
        )
    return CertificateOut(**_row_to_record(row))
