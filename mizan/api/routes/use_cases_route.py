"""Use-case catalogue routes.

GET /api/v1/use-cases                  -- list the government use cases
GET /api/v1/use-cases/{id}             -- one use case with the controls it demands
GET /api/v1/use-cases/{id}/datasets    -- the government datasets grounding it

The records are served from the published register at
suites/controls/use_cases.json and the control register at
suites/controls/controls.json, which are the same files the engine
adjudicates against. Serving the interface from a separate fixture copy
allowed the two to drift, and did drift: the fixture listed one invented
control per use case.

British English throughout.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from mizan.api import bindings, catalogue
from mizan.api.schemas import ControlRow, UseCaseDetail, UseCaseRow

router = APIRouter(prefix="/use-cases", tags=["use-cases"])


def _row(record: dict[str, Any]) -> UseCaseRow:
    return UseCaseRow(
        id=record["id"],
        name_en=record["name_en"],
        name_ar=record["name_ar"],
        description_en=record["description_en"],
        description_ar=record["description_ar"],
        use_case_class=record["use_case_class"],
        confidence_threshold=float(record["confidence_threshold"]),
    )


@router.get("", response_model=list[UseCaseRow], summary="List government use cases")
async def list_use_cases() -> list[UseCaseRow]:
    """Return all available government use cases."""
    return [_row(uc) for uc in catalogue.use_cases()]


@router.get(
    "/{use_case_id}",
    response_model=UseCaseDetail,
    summary="Retrieve a use case with its controls",
)
async def get_use_case(use_case_id: str) -> UseCaseDetail:
    """Return the full use-case record including the controls it demands."""
    record = catalogue.use_case(use_case_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Use case '{use_case_id}' not found.")

    controls: list[ControlRow] = []
    for entry in record.get("controls", []):
        labels = catalogue.control_labels(entry["control_id"])
        controls.append(ControlRow(
            id=entry["control_id"],
            name_en=labels["name_en"],
            name_ar=labels["name_ar"],
            framework_clause=entry.get("framework_clause", labels["framework_clause"]),
            is_mandatory=bool(entry.get("is_mandatory", True)),
            weight=float(entry.get("weight", 1.0)),
            suite_id=entry.get("suite_id", ""),
        ))

    base = _row(record)
    return UseCaseDetail(**base.model_dump(), controls=controls)


@router.get(
    "/{use_case_id}/datasets",
    summary="List the government datasets grounding a use case",
    description=(
        "Each record is read from the manifest written when the dataset was "
        "fetched and hash-verified, so the publishing entity, the resource "
        "identifier and the read date are the ones a fetch actually saw."
    ),
)
async def get_use_case_datasets(use_case_id: str) -> list[dict[str, Any]]:
    """Return the dataset bindings for one use case."""
    if catalogue.use_case(use_case_id) is None:
        raise HTTPException(status_code=404, detail=f"Use case '{use_case_id}' not found.")
    return bindings.bindings_for(use_case_id)
