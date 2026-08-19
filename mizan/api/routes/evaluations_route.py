"""Evaluation routes.

POST /api/v1/evaluations            -- start an evaluation
GET  /api/v1/evaluations/{id}       -- retrieve evaluation status and trail
GET  /api/v1/evaluations            -- list evaluations (optional model_id filter)

Wave 1: real DB writes. POST creates evaluation, use_case, and controls rows.
GET reads from the DB. The evaluation state is also kept in the in-process
_EVAL_STATE dict so the websocket handler can update arm_pulls and stopping_reason
in memory between DB writes.

The websocket handler at /api/v1/ws/evaluations/{id}/stream drives the engine.
British English throughout.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status

from mizan.api import catalogue
from mizan.api.routes import models_route
from mizan.api.schemas import EvaluationIn, EvaluationOut, EvaluationRow

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTROLS_JSON = _REPO_ROOT / "suites" / "controls" / "controls.json"


def _db_path() -> Path:
    """Resolve the database file, honouring MIZAN_DATABASE_URL.

    Read per call rather than captured at import, and read from the same
    environment variable the data-access layer uses. A hardcoded path here made
    the route untestable in isolation: the API tests passed locally against a
    seeded working copy and failed on a clean checkout, which is the same
    non-hermetic defect the corpus determinism test showed.
    """
    url = os.environ.get("MIZAN_DATABASE_URL", "")
    if url.startswith("sqlite") and "///" in url:
        return Path(url.split("///", 1)[1])
    return _REPO_ROOT / "data" / "mizan.db"

# In-process evaluation state. Keyed by evaluation_id.
# Updated by the websocket handler as the engine runs.
# Structure mirrors EvaluationOut fields.
_EVAL_STATE: dict[str, dict] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_evaluation_rows(
    evaluation_id: str,
    model_id: str,
    use_case_id: str,
    engine_config: dict,
) -> None:
    """Insert the use-case, control, and evaluation rows this run needs.

    Uses OR IGNORE for the catalogue rows so repeated POST calls are
    idempotent. The use case is written from the published register in
    suites/controls/use_cases.json rather than from a hardcoded citizen
    chatbot record, so the row in the database says what was actually
    adjudicated. A new evaluation row is always inserted fresh.
    """
    now = _now_iso()
    catalogue_rows = json.loads(_CONTROLS_JSON.read_text(encoding="utf-8"))
    control_rows = catalogue_rows.get("controls", [])

    use_case = catalogue.use_case(use_case_id)

    with closing(sqlite3.connect(str(_db_path()))) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        if use_case is not None:
            conn.execute(
                """
                INSERT OR IGNORE INTO use_cases
                    (id, name_en, name_ar, description_en, description_ar,
                     use_case_class, confidence_threshold, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    use_case["id"],
                    use_case["name_en"],
                    use_case["name_ar"],
                    use_case["description_en"],
                    use_case["description_ar"],
                    use_case["use_case_class"],
                    float(use_case["confidence_threshold"]),
                    now,
                ),
            )

        # Every control in the register is inserted, not only those this use
        # case demands: the evidence table carries a foreign key to controls,
        # and a control row must exist before any probe against it is written.
        for ctrl in control_rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO controls
                    (id, use_case_id, name_en, name_ar, description_en,
                     description_ar, framework_clause, is_mandatory, weight,
                     suite_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ctrl["id"],
                    use_case_id,
                    ctrl["name_en"],
                    ctrl["name_ar"],
                    ctrl["description_en"],
                    ctrl["description_ar"],
                    ctrl.get("framework_clause", "MIZAN-CTL"),
                    1,
                    ctrl.get("weight", 1.0),
                    ctrl["suite_id"],
                    now,
                ),
            )

        conn.execute(
            """
            INSERT INTO evaluations
                (id, model_id, use_case_id, status, arm_pulls, engine_config,
                 started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                model_id,
                use_case_id,
                "pending",
                "[]",
                json.dumps(engine_config),
                now,
            ),
        )
        conn.commit()


def _read_evaluation_from_db(evaluation_id: str) -> dict | None:
    """Read one evaluation row from the DB. Returns None if not found."""
    with closing(sqlite3.connect(str(_db_path()))) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def _list_evaluations_from_db(model_id: str | None) -> list[dict]:
    """List evaluation rows from DB, optionally filtered by model_id."""
    with closing(sqlite3.connect(str(_db_path()))) as conn:
        conn.row_factory = sqlite3.Row
        if model_id:
            rows = conn.execute(
                "SELECT * FROM evaluations WHERE model_id = ? ORDER BY started_at DESC",
                (model_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM evaluations ORDER BY started_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


@router.post(
    "",
    response_model=EvaluationOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an evaluation",
    description=(
        "Start an adaptive evaluation of a registered model against a "
        "government use case. Returns immediately with the evaluation "
        "record in 'running' state. Stream progress via the WebSocket "
        "endpoint /api/v1/ws/evaluations/{id}/stream."
    ),
)
async def start_evaluation(body: EvaluationIn) -> EvaluationOut:
    """Create the evaluation and catalogue rows; return the initial record.

    The model must already be registered. Its card is carried into the
    in-process record because the harness needs it: several controls are
    decided by attestation against the card, and an evaluation started
    without one fails part-way through with a card-missing error.
    """
    now = _now_iso()
    eval_id = str(uuid.uuid4())

    model_row = models_route.read_model(body.model_id)
    if model_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{body.model_id}' is not registered. Register it first.",
        )

    if catalogue.use_case(body.use_case_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{body.use_case_id}' is not in the register.",
        )

    engine_config = body.engine_config_overrides or {}

    _seed_evaluation_rows(eval_id, body.model_id, body.use_case_id, engine_config)
    models_route.set_status(body.model_id, "in_evaluation")

    record: dict = {
        "id": eval_id,
        "model_id": body.model_id,
        "use_case_id": body.use_case_id,
        "status": "pending",
        "verdict": None,
        "arm_pulls": [],
        "stopping_reason": None,
        "total_queries": 0,
        "engine_config": engine_config,
        "started_at": now,
        "completed_at": None,
        "control_decisions": {},
        # Consumed by the websocket handler; not part of the response schema.
        "model_card": models_route.read_model_card(body.model_id),
        "evaluation_profile": models_route.read_profile(body.model_id),
        "endpoint_url": model_row.get("endpoint_url"),
    }
    _EVAL_STATE[eval_id] = record
    return EvaluationOut(**{k: v for k, v in record.items() if k in EvaluationOut.model_fields})


@router.get(
    "",
    response_model=list[EvaluationRow],
    summary="List evaluations",
)
async def list_evaluations(
    model_id: str | None = Query(default=None, description="Filter by model ID"),
) -> list[EvaluationRow]:
    """Return evaluations, optionally filtered by model ID."""
    rows = _list_evaluations_from_db(model_id)
    result: list[EvaluationRow] = []
    for r in rows:
        result.append(EvaluationRow(
            id=r["id"],
            model_id=r["model_id"],
            use_case_id=r["use_case_id"],
            status=r["status"],
            verdict=r.get("verdict"),
            total_queries=r.get("total_queries", 0),
            started_at=r["started_at"],
            completed_at=r.get("completed_at"),
        ))
    return result


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationOut,
    summary="Retrieve evaluation status and adjudication trail",
)
async def get_evaluation(evaluation_id: str) -> EvaluationOut:
    """Return the full evaluation record including the bandit arm-pull trail."""
    # Prefer in-process state (has live arm_pulls list) over DB.
    if evaluation_id in _EVAL_STATE:
        record = _EVAL_STATE[evaluation_id]
        return EvaluationOut(**{k: v for k, v in record.items() if k in EvaluationOut.model_fields})

    row = _read_evaluation_from_db(evaluation_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Evaluation '{evaluation_id}' not found.")

    arm_pulls_raw = row.get("arm_pulls") or "[]"
    try:
        arm_pulls = json.loads(arm_pulls_raw)
    except (json.JSONDecodeError, TypeError):
        arm_pulls = []

    engine_config_raw = row.get("engine_config") or "{}"
    try:
        engine_config = json.loads(engine_config_raw)
    except (json.JSONDecodeError, TypeError):
        engine_config = {}

    return EvaluationOut(
        id=row["id"],
        model_id=row["model_id"],
        use_case_id=row["use_case_id"],
        status=row["status"],
        verdict=row.get("verdict"),
        arm_pulls=arm_pulls,
        stopping_reason=row.get("stopping_reason"),
        total_queries=row.get("total_queries", 0),
        engine_config=engine_config,
        started_at=row["started_at"],
        completed_at=row.get("completed_at"),
        # control_decisions is not stored in the evaluations table; it is
        # available only from _EVAL_STATE (populated by the websocket handler).
        control_decisions={},
    )
