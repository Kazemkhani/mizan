"""WebSocket endpoint for streaming evaluation traces.

WS /api/v1/ws/evaluations/{evaluation_id}/stream

The contract is fixed here in Wave 0 so that:
  - Wave 3 (ATELIER) can build the live evaluation theatre against it.
  - Wave 1 (BANDIT/HARNESS) can emit StreamEvent objects as they run.

Protocol:
  1. Client connects via WebSocket.
  2. Server sends StreamEvent JSON objects as evaluation progresses.
  3. On evaluation completion, the server sends a final 'stop' event and
     closes the connection.
  4. On error, the server sends an 'error' event before closing.

In Wave 0 the handler sends a short synthetic event sequence as a stub.
Wave 1 replaces the stub body with real engine output.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from mizan.api.schemas import StreamEvent

router = APIRouter(prefix="/ws", tags=["streaming"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.websocket("/evaluations/{evaluation_id}/stream")
async def stream_evaluation(websocket: WebSocket, evaluation_id: str) -> None:
    """Stream evaluation trace events for the given evaluation ID.

    Wave 0 stub: sends three synthetic events then closes.
    Wave 1 replaces this with a real async generator driven by the bandit engine.
    """
    await websocket.accept()
    try:
        # Stub sequence: one arm_pull event, one probe_result event, one stop event.
        stub_events: list[StreamEvent] = [
            StreamEvent(
                event_type="arm_pull",
                evaluation_id=evaluation_id,
                payload={
                    "step": 1,
                    "suite_id": "suite-capability",
                    "arm_index": 0,
                    "reward": 0.0,
                    "ucb_value": 0.0,
                    "posterior_state": {},
                    "cumulative_queries": 0,
                    "note": "Wave 0 stub -- real events wired in Wave 1",
                },
                sequence=1,
                timestamp=_now_iso(),
            ),
            StreamEvent(
                event_type="probe_result",
                evaluation_id=evaluation_id,
                payload={
                    "probe_id": "stub-001",
                    "score": 0.0,
                    "passed": False,
                    "note": "Wave 0 stub",
                },
                sequence=2,
                timestamp=_now_iso(),
            ),
            StreamEvent(
                event_type="stop",
                evaluation_id=evaluation_id,
                payload={
                    "status": "pending",
                    "verdict": None,
                    "stopping_reason": "stub",
                    "note": "Wave 0 stub -- real stopping logic wired in Wave 1",
                },
                sequence=3,
                timestamp=_now_iso(),
            ),
        ]

        for event in stub_events:
            await websocket.send_text(event.model_dump_json())
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        pass
    finally:
        # Ensure the socket is closed; ignore errors if already closed.
        try:
            await websocket.close()
        except Exception:
            pass
