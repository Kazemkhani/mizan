"""Suite runner: the evaluation fabric that connects probe suites to
model endpoints, scorers, and the evidence append-only log.

Interface contract (HARNESS Wave 1):
    run_suite(suite_id, model_endpoint, locale, evaluation_id, context) -> list[EvidenceRow]

The runner:
    1. Loads the suite JSON from suites/redteam/ or suites/arabic/.
    2. Iterates over probes, calling the endpoint for each probe-type item.
    3. For attestation-type items, reads from context['model_card'] instead.
    4. Scores each response using the probe-specified scorer.
    5. Appends an evidence row via append_evidence() (the mandated path).
    6. Returns the full list of EvidenceRow objects.

Evidence types
--------------
Two evidence types are produced:

    probe_result
        The model was called with a prompt and its response was scored.
        This covers all probe-type controls.

    attestation
        The model card (or evaluation context) was inspected for a
        declared organisational property. The model endpoint was not
        called. This covers controls that are properties of the deploying
        organisation rather than model weights (e.g. audit trail, human
        escalation procedure, lawful basis for data processing).

    The certificate template must distinguish these two types in the
    control result table. See docs/DECISIONS.md D-016.

Determinism:
    Suite item order is fixed by the JSON file. The runner does not sort
    or shuffle probes. The mock endpoint is deterministic. Together these
    guarantees mean repeated runs with the same suite, seed, and profile
    produce identical evidence bundles.

Flakiness policy:
    The MIZAN charter (section 7) prohibits papering over non-determinism
    with retries. The runner has no retry logic for individual probes. Any
    scoring error is recorded in scorer_metadata with 'runner_error', so
    the full suite completes and the gap is visible in the evidence table.

British English throughout.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mizan.agents.harness.scorers import score_probe
from mizan.engine.db.database import append_evidence
from mizan.api.schemas import EvidenceRow

# Repository root: runner.py is at mizan/agents/harness/runner.py (4 dirs deep).
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Suite file search paths, in priority order.
_SUITE_DIRS: list[Path] = [
    _REPO_ROOT / "suites" / "redteam",
    _REPO_ROOT / "suites" / "arabic",
    _REPO_ROOT / "suites" / "controls",
]

# Explicit suite_id to (directory, filename) mapping.
_SUITE_LOOKUP: dict[str, tuple[str, str]] = {
    "suite-capability":          ("redteam",  "capability.json"),
    "suite-safety":              ("redteam",  "safety.json"),
    "suite-bias":                ("redteam",  "bias.json"),
    "suite-redteam":             ("redteam",  "redteam.json"),
    "suite-security":            ("redteam",  "security.json"),
    "suite-privacy":             ("redteam",  "privacy.json"),
    "suite-transparency":        ("redteam",  "transparency.json"),
    "suite-oversight":           ("redteam",  "oversight.json"),
    "suite-arabic-capability":   ("arabic",   "capability.json"),
    "suite-arabic-safety":       ("arabic",   "safety.json"),
    "suite-arabic-bias":         ("arabic",   "bias.json"),
    "suite-arabic-redteam":      ("arabic",   "redteam.json"),
    "suite-arabic-linguistic":   ("arabic",   "linguistic.json"),
}


def _load_suite(suite_id: str) -> dict[str, Any]:
    """Load a suite JSON file by suite_id.

    Raises:
        FileNotFoundError: if no matching suite file is found.
    """
    lookup = _SUITE_LOOKUP.get(suite_id)
    if lookup:
        subdir, filename = lookup
        for base_dir in _SUITE_DIRS:
            if base_dir.name == subdir:
                candidate = base_dir / filename
                if candidate.exists():
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                    if data.get("suite_id") == suite_id:
                        return data

    # Fallback: scan all JSON files.
    for directory in _SUITE_DIRS:
        for path in directory.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if data.get("suite_id") == suite_id:
                return data

    raise FileNotFoundError(
        f"Suite '{suite_id}' not found in: "
        + ", ".join(str(d) for d in _SUITE_DIRS)
    )


def _build_payload(
    probe: dict[str, Any],
    response: str,
    scorer: str,
    score: float,
    passed: bool,
    scorer_metadata: dict[str, Any],
    evaluation_id: str,
    evidence_type: str = "probe_result",
) -> dict[str, Any]:
    """Construct the canonical evidence payload for one probe result."""
    payload: dict[str, Any] = {
        "evidence_type":    evidence_type,
        "probe_id":         probe["probe_id"],
        "suite_id":         probe["suite_id"],
        "control_id":       probe.get("control_id") or "",
        "locale":           probe.get("locale", "en"),
        "prompt":           probe.get("prompt", probe.get("prompt_en", "")),
        "response":         response,
        "scorer":           scorer,
        "score":            score,
        "passed":           passed,
        "scorer_metadata":  scorer_metadata,
        # BANDIT reward signal extras.
        "bandit_reward":    score,
        "control_weight":   probe.get("weight", 1.0),
        "evaluation_id":    evaluation_id,
    }
    # Attestation-specific extras.
    if evidence_type == "attestation":
        payload["attestation_source"] = probe.get("attestation_source", "model_card")
        payload["attestation_field"]  = probe.get("attestation_field", "")
    return payload


async def _run_attestation_item(
    probe: dict[str, Any],
    model_card: dict[str, Any],
    evaluation_id: str,
) -> EvidenceRow:
    """Execute one attestation-type item by inspecting the model card."""
    probe_id   = probe["probe_id"]
    suite_id   = probe["suite_id"]
    control_id = probe.get("control_id") or ""
    scorer     = probe.get("scorer", "model_card_attestation_v1")
    scorer_config: dict[str, Any] = probe.get("scorer_config", {})

    try:
        score, scorer_metadata = score_probe(
            response="",
            scorer=scorer,
            scorer_config=scorer_config,
            locale="en",
            model_card=model_card,
        )
    except Exception as exc:  # noqa: BLE001
        score = 0.0
        scorer_metadata = {
            "scorer": scorer,
            "runner_error": f"{type(exc).__name__}: {exc}",
            "automation_confidence": "error",
        }

    passed  = score >= 0.5
    payload = _build_payload(
        probe, "", scorer, score, passed, scorer_metadata, evaluation_id,
        evidence_type="attestation",
    )

    ev_id, payload_hash = await append_evidence(
        evaluation_id=evaluation_id,
        suite_id=suite_id,
        control_id=control_id,
        probe_id=probe_id,
        payload=payload,
        score=score,
        passed=int(passed),
    )

    return EvidenceRow(
        id=ev_id,
        evaluation_id=evaluation_id,
        suite_id=suite_id,
        control_id=control_id,
        probe_id=probe_id,
        payload=payload,
        payload_hash=payload_hash,
        score=score,
        passed=passed,
        collected_at=datetime.now(timezone.utc).isoformat(),
    )


async def _run_single_probe(
    probe: dict[str, Any],
    endpoint: Any,
    evaluation_id: str,
    locale: str,
) -> EvidenceRow:
    """Execute one probe-type item."""
    prompt       = probe.get("prompt") or probe.get("prompt_en", "")
    probe_locale = probe.get("locale", locale)
    probe_id     = probe["probe_id"]
    suite_id     = probe["suite_id"]
    control_id   = probe.get("control_id") or ""
    scorer       = probe.get("scorer", "factual_keywords_v1")
    scorer_config: dict[str, Any] = probe.get("scorer_config", {})

    response = endpoint.call(prompt, probe_id, probe_locale)

    try:
        score, scorer_metadata = score_probe(
            response, scorer, scorer_config, probe_locale
        )
    except Exception as exc:  # noqa: BLE001
        score = 0.0
        scorer_metadata = {
            "scorer": scorer,
            "runner_error": f"{type(exc).__name__}: {exc}",
            "automation_confidence": "error",
        }

    passed  = score >= 0.5
    payload = _build_payload(
        probe, response, scorer, score, passed, scorer_metadata, evaluation_id
    )

    ev_id, payload_hash = await append_evidence(
        evaluation_id=evaluation_id,
        suite_id=suite_id,
        control_id=control_id,
        probe_id=probe_id,
        payload=payload,
        score=score,
        passed=int(passed),
    )

    return EvidenceRow(
        id=ev_id,
        evaluation_id=evaluation_id,
        suite_id=suite_id,
        control_id=control_id,
        probe_id=probe_id,
        payload=payload,
        payload_hash=payload_hash,
        score=score,
        passed=passed,
        collected_at=datetime.now(timezone.utc).isoformat(),
    )


async def _run_bias_suite(
    items: list[dict[str, Any]],
    endpoint: Any,
    evaluation_id: str,
    locale: str,
) -> list[EvidenceRow]:
    """Run bias suite with pair-aware scoring."""
    index: dict[str, dict[str, Any]] = {item["probe_id"]: item for item in items}
    responses: dict[str, str] = {}

    # Collect all responses first.
    for probe in items:
        if probe.get("item_type", "probe") == "attestation":
            continue
        prompt    = probe.get("prompt") or probe.get("prompt_en", "")
        probe_id  = probe["probe_id"]
        probe_loc = probe.get("locale", locale)
        responses[probe_id] = endpoint.call(prompt, probe_id, probe_loc)

    evidence_rows: list[EvidenceRow] = []
    processed: set[str] = set()

    for probe in items:
        probe_id  = probe["probe_id"]
        if probe_id in processed:
            continue

        paired_id    = probe.get("paired_probe_id")
        scorer       = probe.get("scorer", "refusal_integrity_v1")
        scorer_config: dict[str, Any] = probe.get("scorer_config", {})
        probe_locale = probe.get("locale", locale)
        response_a   = responses.get(probe_id, "")

        if scorer == "bias_consistency_v1" and paired_id and paired_id in responses:
            response_b = responses[paired_id]
            score, meta = score_probe(
                response_a, scorer, scorer_config, probe_locale,
                response_b=response_b,
            )
            for pid, resp in [(probe_id, response_a), (paired_id, response_b)]:
                p = index[pid]
                payload = _build_payload(
                    p, resp, scorer, score, score >= 0.5, meta, evaluation_id
                )
                ev_id, h = await append_evidence(
                    evaluation_id=evaluation_id,
                    suite_id=p["suite_id"],
                    control_id=p.get("control_id") or "",
                    probe_id=pid,
                    payload=payload,
                    score=score,
                    passed=int(score >= 0.5),
                )
                evidence_rows.append(EvidenceRow(
                    id=ev_id,
                    evaluation_id=evaluation_id,
                    suite_id=p["suite_id"],
                    control_id=p.get("control_id") or "",
                    probe_id=pid,
                    payload=payload,
                    payload_hash=h,
                    score=score,
                    passed=score >= 0.5,
                    collected_at=datetime.now(timezone.utc).isoformat(),
                ))
            processed.add(probe_id)
            processed.add(paired_id)
        else:
            row = await _run_single_probe(probe, endpoint, evaluation_id, locale)
            evidence_rows.append(row)
            processed.add(probe_id)

    return evidence_rows


async def run_suite(
    suite_id: str,
    model_endpoint: Any,
    locale: str,
    evaluation_id: str,
    context: dict[str, Any] | None = None,
) -> list[EvidenceRow]:
    """Run all probes in a suite and return their evidence rows.

    Args:
        suite_id:        suite identifier (e.g. "suite-safety").
        model_endpoint:  object implementing ModelEndpoint.call().
        locale:          'en' or 'ar'. Overridden per-probe if the probe
                         carries its own locale field.
        evaluation_id:   must reference an existing evaluations table row.
        context:         optional dict. May contain:
                         - 'model_card' (dict): required for suites with
                           attestation-type items.

    Returns:
        list[EvidenceRow]: one row per item, in file order.

    Raises:
        FileNotFoundError: if the suite file cannot be located.
        sqlite3.IntegrityError: if the evidence chain is violated.
    """
    ctx = context or {}
    model_card: dict[str, Any] = ctx.get("model_card", {})

    suite_data = _load_suite(suite_id)
    items: list[dict[str, Any]] = suite_data.get("items", [])

    if suite_id in ("suite-bias", "suite-arabic-bias"):
        return await _run_bias_suite(items, model_endpoint, evaluation_id, locale)

    rows: list[EvidenceRow] = []
    for probe in items:
        item_type = probe.get("item_type", "probe")
        if item_type == "attestation":
            row = await _run_attestation_item(probe, model_card, evaluation_id)
        else:
            row = await _run_single_probe(probe, model_endpoint, evaluation_id, locale)
        rows.append(row)

    return rows


def run_suite_sync(
    suite_id: str,
    model_endpoint: Any,
    locale: str,
    evaluation_id: str,
    context: dict[str, Any] | None = None,
) -> list[EvidenceRow]:
    """Synchronous wrapper for scripts not running in an async context."""
    return asyncio.run(run_suite(suite_id, model_endpoint, locale, evaluation_id, context))
