"""Model registry routes.

POST   /api/v1/models          -- submit a model for registration
GET    /api/v1/models          -- list all registered models
GET    /api/v1/models/{id}     -- retrieve a single model record

Handlers return fixture data in Wave 0. Wave 1 (BANDIT/HARNESS) wires
the real database calls using the data-access layer in mizan.engine.db.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from mizan.api.schemas import ModelIn, ModelOut, ModelRow

router = APIRouter(prefix="/models", tags=["models"])

# ---------------------------------------------------------------------------
# Wave 0 fixture store. Wave 1 replaces this with real DB calls.
# ---------------------------------------------------------------------------
_FIXTURE_STORE: dict[str, dict] = {}


@router.post(
    "",
    response_model=ModelOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a model",
    description=(
        "Submit an AI model for registration in the MIZAN registry. "
        "The model enters the 'pending' lifecycle state and is eligible "
        "for evaluation once a use case is specified."
    ),
)
async def register_model(body: ModelIn) -> ModelOut:
    """Register a new model. Returns the created model record."""
    now = datetime.now(timezone.utc).isoformat()
    model_id = str(uuid.uuid4())
    record = {
        "id": model_id,
        "name_en": body.name_en,
        "name_ar": body.name_ar,
        "provider": body.provider,
        "version": body.version,
        "endpoint_url": body.endpoint_url,
        "model_card": body.model_card.model_dump(),
        "status": "pending",
        "submitted_at": now,
        "updated_at": now,
    }
    _FIXTURE_STORE[model_id] = record
    return ModelOut(**record)


@router.get(
    "",
    response_model=list[ModelRow],
    summary="List registered models",
)
async def list_models() -> list[ModelRow]:
    """Return all registered models as lightweight row records."""
    return [
        ModelRow(
            id=r["id"],
            name_en=r["name_en"],
            name_ar=r["name_ar"],
            provider=r["provider"],
            version=r["version"],
            status=r["status"],
            submitted_at=r["submitted_at"],
        )
        for r in _FIXTURE_STORE.values()
    ]


@router.get(
    "/{model_id}",
    response_model=ModelOut,
    summary="Retrieve a model record",
)
async def get_model(model_id: str) -> ModelOut:
    """Return the full record for a single registered model."""
    record = _FIXTURE_STORE.get(model_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return ModelOut(**record)
