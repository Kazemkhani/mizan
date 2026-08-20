"""Model registry routes.

POST   /api/v1/models          -- submit a model for registration
GET    /api/v1/models          -- list all registered models
GET    /api/v1/models/{id}     -- retrieve a single model record

Records are held in the models table rather than in process memory, so a
seeded registry is visible to the interface and a submission survives an API
restart. Every write goes through mizan.api.store.

British English throughout.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status

from mizan.api import store
from mizan.api.schemas import ModelIn, ModelOut, ModelRow

router = APIRouter(prefix="/models", tags=["models"])

# The declared mock profile is carried inside the model card JSON under this
# key. The models table has no column for it and the schema is fixed by
# engine/db/schema.sql, so the card, which is already a free-form JSON
# document, is the correct place to record a submission-time declaration.
_PROFILE_KEY = "mizan_evaluation_profile"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _card_of(row: dict[str, Any]) -> dict[str, Any]:
    """Parse the stored model card, tolerating a malformed record."""
    try:
        card = json.loads(row.get("model_card") or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return card if isinstance(card, dict) else {}


def _to_out(row: dict[str, Any]) -> ModelOut:
    card = _card_of(row)
    profile = card.get(_PROFILE_KEY, "compliant")
    if profile not in ("compliant", "non_compliant"):
        profile = "compliant"
    return ModelOut(
        id=row["id"],
        name_en=row["name_en"],
        name_ar=row["name_ar"],
        provider=row["provider"],
        version=row["version"],
        endpoint_url=row.get("endpoint_url"),
        evaluation_profile=profile,
        model_card=card,
        status=row["status"],
        submitted_at=row["submitted_at"],
        updated_at=row["updated_at"],
    )


def read_model(model_id: str) -> dict[str, Any] | None:
    """Return one model row, used by the evaluation routes."""
    return store.query_one("SELECT * FROM models WHERE id = ?", (model_id,))


def read_model_card(model_id: str) -> dict[str, Any]:
    """Return the stored model card for a model, empty when unknown."""
    row = read_model(model_id)
    return _card_of(row) if row else {}


def read_profile(model_id: str) -> str:
    """Return the declared mock profile for a model, defaulting to compliant."""
    card = read_model_card(model_id)
    profile = card.get(_PROFILE_KEY, "compliant")
    return profile if profile in ("compliant", "non_compliant") else "compliant"


def set_status(model_id: str, new_status: str) -> None:
    """Advance the lifecycle state of a model record."""
    store.execute(
        "UPDATE models SET status = ?, updated_at = ? WHERE id = ?",
        (new_status, _now(), model_id),
    )


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
    now = _now()
    model_id = str(uuid.uuid4())

    card = body.model_card.model_dump()
    card[_PROFILE_KEY] = body.evaluation_profile

    store.execute(
        """
        INSERT INTO models
            (id, name_en, name_ar, provider, version, endpoint_url,
             model_card, status, submitted_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            model_id,
            body.name_en,
            body.name_ar,
            body.provider,
            body.version,
            body.endpoint_url,
            json.dumps(card, ensure_ascii=False),
            "pending",
            now,
            now,
        ),
    )

    row = read_model(model_id)
    if row is None:
        raise HTTPException(status_code=500, detail="Model record could not be written.")
    return _to_out(row)


@router.get(
    "",
    response_model=list[ModelRow],
    summary="List registered models",
)
async def list_models() -> list[ModelRow]:
    """Return all registered models, most recently submitted first."""
    rows = store.query("SELECT * FROM models ORDER BY submitted_at DESC")
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
        for r in rows
    ]


@router.get(
    "/{model_id}",
    response_model=ModelOut,
    summary="Retrieve a model record",
)
async def get_model(model_id: str) -> ModelOut:
    """Return the full record for a single registered model."""
    row = read_model(model_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return _to_out(row)
