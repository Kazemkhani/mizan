"""Evaluation routes.

POST /api/v1/evaluations            -- start an evaluation
GET  /api/v1/evaluations/{id}       -- retrieve evaluation status and trail
GET  /api/v1/evaluations            -- list evaluations (optional model_id filter)

Handlers return fixture data in Wave 0. Wave 1 (BANDIT) wires the real
bandit engine via the mizan.engine.bandit module.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from mizan.api.schemas import EvaluationIn, EvaluationOut, EvaluationRow

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

_FIXTURE_STORE: dict[str, dict] = {}


@router.post(
    "",
    response_model=EvaluationOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an evaluation",
    description=(
        "Start an adaptive evaluation of a registered model against a "
        "government use case. Returns immediately with the evaluation "
        "record in 'pending' state. Stream progress via the WebSocket "
        "endpoint /api/v1/ws/evaluations/{id}/stream."
    ),
)
async def start_evaluation(body: EvaluationIn) -> EvaluationOut:
    """Start an evaluation and return the initial record."""
    now = datetime.now(timezone.utc).isoformat()
    eval_id = str(uuid.uuid4())
    record = {
        "id": eval_id,
        "model_id": body.model_id,
        "use_case_id": body.use_case_id,
        "status": "pending",
        "verdict": None,
        "arm_pulls": [],
        "stopping_reason": None,
        "total_queries": 0,
        "engine_config": body.engine_config_overrides,
        "started_at": now,
        "completed_at": None,
    }
    _FIXTURE_STORE[eval_id] = record
    return EvaluationOut(**record)


@router.get(
    "",
    response_model=list[EvaluationRow],
    summary="List evaluations",
)
async def list_evaluations(
    model_id: str | None = Query(default=None, description="Filter by model ID"),
) -> list[EvaluationRow]:
    """Return evaluations, optionally filtered by model ID."""
    records = _FIXTURE_STORE.values()
    if model_id:
        records = [r for r in records if r["model_id"] == model_id]
    return [
        EvaluationRow(
            id=r["id"],
            model_id=r["model_id"],
            use_case_id=r["use_case_id"],
            status=r["status"],
            verdict=r["verdict"],
            total_queries=r["total_queries"],
            started_at=r["started_at"],
            completed_at=r["completed_at"],
        )
        for r in records
    ]


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationOut,
    summary="Retrieve evaluation status and adjudication trail",
)
async def get_evaluation(evaluation_id: str) -> EvaluationOut:
    """Return the full evaluation record including the bandit arm-pull trail."""
    record = _FIXTURE_STORE.get(evaluation_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Evaluation '{evaluation_id}' not found.")
    return EvaluationOut(**record)
