"""WebSocket endpoint for streaming evaluation traces.

WS /api/v1/ws/evaluations/{evaluation_id}/stream

Protocol:
  1. Client connects via WebSocket.
  2. Server sends StreamEvent JSON objects as evaluation progresses.
  3. On evaluation completion, the server sends a final 'stop' event and
     closes the connection.
  4. On error, the server sends an 'error' event before closing.

Wave 1: real engine output. The handler:
  - Loads controls from suites/controls/controls.json.
  - Creates a BatchSuiteRunner (compliant profile for demonstration).
  - Creates a BanditEngine with those controls.
  - Runs engine.run_sync(wrapped_runner) in asyncio.to_thread().
  - The wrapped runner puts an arm_pull StreamEvent into an asyncio.Queue after
    each probe. The websocket handler drains that queue concurrently.
  - On completion, a stop event with the verdict and stopping_reason is sent.

Thread safety:
  engine.run_sync() runs in a worker thread via asyncio.to_thread(). The
  wrapped_runner.__call__ is called from that thread. To push StreamEvent
  objects into the asyncio.Queue from the thread, it uses
  loop.call_soon_threadsafe(queue.put_nowait, event), which is the correct
  pattern for crossing the thread/event-loop boundary.

British English throughout.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from mizan.agents.harness.adapters import MockEndpoint
from mizan.agents.harness.batch_runner import BatchSuiteRunner
from mizan.api import catalogue, certificate as certificate_issuer, store
from mizan.api.routes import models_route
from mizan.api.routes.evaluations_route import _EVAL_STATE
from mizan.api.schemas import ArmPull, StreamEvent
from mizan.engine.bandit.allocator import BanditEngine

router = APIRouter(prefix="/ws", tags=["streaming"])

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTROLS_JSON = _REPO_ROOT / "suites" / "controls" / "controls.json"
_SENTINEL = object()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_controls() -> list[dict]:
    """Load the control catalogue from the canonical JSON file."""
    catalogue = json.loads(_CONTROLS_JSON.read_text(encoding="utf-8"))
    return catalogue.get("controls", [])


def _make_controls_list(controls_raw: list[dict]) -> list[dict]:
    """Convert catalogue records to the format BanditEngine expects."""
    return [
        {
            "control_id":          c["id"],
            "suite_id":            c["suite_id"],
            "is_mandatory":        True,
            "pass_threshold":      float(c.get("pass_threshold", 0.85)),
            "threshold_direction": c.get("threshold_direction", "above"),
            "weight":              float(c.get("weight", 1.0)),
        }
        for c in controls_raw
    ]


class _WrappedRunner:
    """Wraps BatchSuiteRunner to emit a StreamEvent per arm pull into a queue.

    Called from a worker thread (engine.run_sync runs in asyncio.to_thread).
    Uses loop.call_soon_threadsafe to push events into the asyncio.Queue
    without race conditions.
    """

    def __init__(
        self,
        inner: BatchSuiteRunner,
        evaluation_id: str,
        loop: asyncio.AbstractEventLoop,
        queue: "asyncio.Queue[object]",
    ) -> None:
        self._inner = inner
        self._eval_id = evaluation_id
        self._loop = loop
        self._queue = queue
        self._seq = 0

    def __call__(self, suite_id: str, control_ids: list[str]) -> list[dict]:
        results = self._inner(suite_id, control_ids)
        self._seq += 1
        seq = self._seq

        # Build the ArmPull payload from the first result (one probe per pull).
        payload_dict: dict = {
            "step":               seq,
            "suite_id":           suite_id,
            "arm_index":          0,
            "reward":             results[0]["score"] if results else 0.0,
            "ucb_value":          0.0,
            "posterior_state":    {},
            "cumulative_queries": seq,
        }
        if results:
            first = results[0]
            probe_payload = first.get("payload", {}) or {}
            payload_dict.update({
                "probe_id":     first.get("probe_id", ""),
                "control_id":   first.get("control_id", ""),
                "passed":       first.get("passed", False),
                "score":        round(float(first.get("score", 0.0)), 4),
                "locale":       probe_payload.get("locale", "en"),
                "prompt":       probe_payload.get("prompt", "")[:600],
                "response":     probe_payload.get("response", "")[:600],
                "scorer":       probe_payload.get("scorer", ""),
                "evidence_type": probe_payload.get("evidence_type", "probe_result"),
                "payload_hash": first.get("payload_hash", ""),
            })

        event = StreamEvent(
            event_type="arm_pull",
            evaluation_id=self._eval_id,
            payload=payload_dict,
            sequence=seq,
            timestamp=_now_iso(),
        )
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
        return results


@router.websocket("/evaluations/{evaluation_id}/stream")
async def stream_evaluation(websocket: WebSocket, evaluation_id: str) -> None:
    """Stream evaluation trace events for the given evaluation ID.

    Creates a BanditEngine, drives it through BatchSuiteRunner, and emits
    one arm_pull StreamEvent per probe, then a stop event on completion.
    """
    await websocket.accept()
    try:
        # ------------------------------------------------------------------
        # Validate the evaluation record exists.
        # ------------------------------------------------------------------
        record = _EVAL_STATE.get(evaluation_id)
        if record is None:
            error_event = StreamEvent(
                event_type="error",
                evaluation_id=evaluation_id,
                payload={"message": f"Evaluation '{evaluation_id}' not found. Call POST /api/v1/evaluations first."},
                sequence=0,
                timestamp=_now_iso(),
            )
            await websocket.send_text(error_event.model_dump_json())
            return

        # ------------------------------------------------------------------
        # Build engine components.
        # ------------------------------------------------------------------
        use_case_id  = record.get("use_case_id", "")
        use_case     = catalogue.use_case(use_case_id)

        # The controls this use case demands, at the thresholds the register
        # sets, rather than the whole register at the chatbot threshold.
        controls_list = catalogue.engine_controls(use_case_id)
        if not controls_list:
            controls_list = _make_controls_list(_load_controls())

        mandatory_ids = {c["control_id"] for c in controls_list if c["is_mandatory"]}

        # A submission with no live endpoint is served by the deterministic
        # mock under the profile the submitter declared. The profile is
        # recorded on the certificate face, so a reader can tell how the
        # evaluation was served.
        profile = record.get("evaluation_profile", "compliant")
        if profile not in ("compliant", "non_compliant"):
            profile = "compliant"
        endpoint = MockEndpoint(profile=profile, seed=42)

        # Mark evaluation as running once the websocket connects.
        if evaluation_id in _EVAL_STATE:
            _EVAL_STATE[evaluation_id]["status"] = "running"

        batch_runner = BatchSuiteRunner(
            endpoint=endpoint,
            evaluation_id=evaluation_id,
            locale="en",
            mandatory_control_ids=mandatory_ids,
            model_card=record.get("model_card", {}),
        )

        engine_config = record.get("engine_config") or {}
        engine_config.setdefault("random_seed", 42)
        # No probe caps are imposed here. The caps that were previously set
        # for the API demo (ten probes per control, one hundred and fifty in
        # total) stopped controls short of the bound they would otherwise
        # have earned, so an evaluation served through the API reported a
        # different verdict from the same evaluation run offline. The budget
        # the engine derives from the use case's confidence threshold is the
        # one that governs, and a caller may still override it per
        # evaluation through engine_config_overrides.

        engine = BanditEngine(
            evaluation_id=evaluation_id,
            use_case_class=(use_case or {}).get("use_case_class", "citizen_chatbot"),
            confidence_threshold=float((use_case or {}).get("confidence_threshold", 0.97)),
            controls=controls_list,
            engine_config=engine_config,
        )

        # ------------------------------------------------------------------
        # Thread-safe event queue.
        # ------------------------------------------------------------------
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()
        wrapped = _WrappedRunner(batch_runner, evaluation_id, loop, queue)

        # ------------------------------------------------------------------
        # Run engine in a thread; drain queue concurrently.
        # ------------------------------------------------------------------
        engine_task = asyncio.create_task(
            asyncio.to_thread(engine.run_sync, wrapped)
        )

        # Drain events until the engine finishes.
        while not engine_task.done() or not queue.empty():
            try:
                event_obj = await asyncio.wait_for(queue.get(), timeout=0.05)
                if isinstance(event_obj, StreamEvent):
                    await websocket.send_text(event_obj.model_dump_json())
                    queue.task_done()
            except asyncio.TimeoutError:
                continue

        # ------------------------------------------------------------------
        # Collect the result and update in-process state.
        # ------------------------------------------------------------------
        exc = engine_task.exception()
        if exc is not None:
            error_event = StreamEvent(
                event_type="error",
                evaluation_id=evaluation_id,
                payload={"message": f"Engine error: {type(exc).__name__}: {exc}"},
                sequence=wrapped._seq + 1,
                timestamp=_now_iso(),
            )
            await websocket.send_text(error_event.model_dump_json())
            if evaluation_id in _EVAL_STATE:
                _EVAL_STATE[evaluation_id]["status"] = "failed"
            store.execute(
                "UPDATE evaluations SET status = ? WHERE id = ?",
                ("failed", evaluation_id),
            )
            return

        arm_pulls_result, stopping_reason, verdict = engine_task.result()

        # Serialise arm_pulls to the schema list for _EVAL_STATE.
        arm_pulls_schema = [
            ArmPull(
                step=ap.step,
                suite_id=ap.suite_id,
                arm_index=ap.arm_index,
                reward=ap.reward,
                ucb_value=ap.ucb_value,
                # posterior_state is already a dict[str, dict] from ArmState.to_posterior_snapshot().
                posterior_state=ap.posterior_state,
                cumulative_queries=ap.cumulative_queries,
            )
            for ap in arm_pulls_result
        ]

        control_decisions = engine.control_states()

        completed_at = _now_iso()

        if evaluation_id in _EVAL_STATE:
            _EVAL_STATE[evaluation_id].update({
                "status":           "completed",
                "verdict":          verdict,
                "arm_pulls":        [a.model_dump() for a in arm_pulls_schema],
                "stopping_reason":  stopping_reason,
                "total_queries":    wrapped._seq,
                "completed_at":     completed_at,
                "control_decisions": control_decisions,
            })

        # The evaluation row is written at POST time and updated here, so the
        # trail survives a restart and a later reader sees the same verdict
        # the stream reported.
        store.execute(
            """
            UPDATE evaluations
               SET status = ?, verdict = ?, arm_pulls = ?, stopping_reason = ?,
                   total_queries = ?, completed_at = ?
             WHERE id = ?
            """,
            (
                "completed",
                verdict,
                json.dumps([a.model_dump() for a in arm_pulls_schema]),
                stopping_reason,
                wrapped._seq,
                completed_at,
                evaluation_id,
            ),
        )

        model_id = record.get("model_id", "")
        models_route.set_status(
            model_id, "certified" if verdict == "certified" else "rejected"
        )

        certificate = certificate_issuer.issue(
            evaluation_id=evaluation_id,
            model_id=model_id,
            use_case_id=use_case_id,
            verdict=verdict,
            control_decisions=control_decisions,
            stopping_reason=stopping_reason,
            total_queries=wrapped._seq,
            evaluation_profile=profile,
            endpoint_url=record.get("endpoint_url"),
        )

        # ------------------------------------------------------------------
        # Send the stop event.
        # ------------------------------------------------------------------
        stop_event = StreamEvent(
            event_type="stop",
            evaluation_id=evaluation_id,
            payload={
                "status":          "completed",
                "verdict":         verdict,
                "stopping_reason": stopping_reason,
                "total_queries":   wrapped._seq,
                "control_decisions": control_decisions,
                "certificate_id":  certificate["id"],
                "evidence_bundle_hash": certificate["evidence_bundle_hash"],
            },
            sequence=wrapped._seq + 1,
            timestamp=_now_iso(),
        )
        await websocket.send_text(stop_event.model_dump_json())

    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        try:
            error_event = StreamEvent(
                event_type="error",
                evaluation_id=evaluation_id,
                payload={"message": f"Unhandled error: {type(exc).__name__}: {exc}"},
                sequence=0,
                timestamp=_now_iso(),
            )
            await websocket.send_text(error_event.model_dump_json())
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
