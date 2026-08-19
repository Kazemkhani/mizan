"""Read-only access to the control register and the use-case catalogue.

The canonical files are:

    suites/controls/controls.json    the 36 controls, with pass thresholds
    suites/controls/use_cases.json   the five government use cases, each
                                     naming the controls it demands, with
                                     per-use-case weights and mandatory flags

The API previously ran every evaluation against the full control register at
the citizen-chatbot threshold, whichever use case the caller selected. This
module supplies the per-use-case control set the register already defines, so
a submission against document summarisation is adjudicated against the
controls that use case demands and no others.

Both files are read once and cached; they are build artefacts, not state.

British English throughout.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTROLS_JSON = _REPO_ROOT / "suites" / "controls" / "controls.json"
_USE_CASES_JSON = _REPO_ROOT / "suites" / "controls" / "use_cases.json"

_DEFAULT_PASS_THRESHOLD = 0.85


@lru_cache(maxsize=1)
def control_register() -> dict[str, dict[str, Any]]:
    """Return the full control register keyed by control id."""
    catalogue = json.loads(_CONTROLS_JSON.read_text(encoding="utf-8"))
    return {c["id"]: c for c in catalogue.get("controls", [])}


@lru_cache(maxsize=1)
def use_cases() -> list[dict[str, Any]]:
    """Return the five use cases as published in the register."""
    catalogue = json.loads(_USE_CASES_JSON.read_text(encoding="utf-8"))
    return list(catalogue.get("use_cases", []))


def use_case(use_case_id: str) -> dict[str, Any] | None:
    """Return one use case by id, or None when the id is unknown."""
    for record in use_cases():
        if record["id"] == use_case_id:
            return record
    return None


def engine_controls(use_case_id: str) -> list[dict[str, Any]]:
    """Return the control list for a use case in the shape BanditEngine expects.

    Each entry carries the pass threshold and direction from the control
    register, and the weight and mandatory flag the use case assigns to it.
    An unknown use case falls back to the full register, so a caller
    experimenting with an unregistered identifier still gets an evaluation
    rather than an empty control set.
    """
    register = control_register()
    record = use_case(use_case_id)

    if record is None:
        selected = [
            {"control_id": cid, "is_mandatory": True, "weight": float(c.get("weight", 1.0))}
            for cid, c in register.items()
        ]
    else:
        selected = [
            {
                "control_id": c["control_id"],
                "is_mandatory": bool(c.get("is_mandatory", True)),
                "weight": float(c.get("weight", 1.0)),
            }
            for c in record.get("controls", [])
            if c["control_id"] in register
        ]

    out: list[dict[str, Any]] = []
    for entry in selected:
        source = register[entry["control_id"]]
        out.append({
            "control_id":          entry["control_id"],
            "suite_id":            source["suite_id"],
            "is_mandatory":        entry["is_mandatory"],
            "pass_threshold":      float(source.get("pass_threshold", _DEFAULT_PASS_THRESHOLD)),
            "threshold_direction": source.get("threshold_direction", "above"),
            "weight":              entry["weight"],
        })
    return out


def control_labels(control_id: str) -> dict[str, str]:
    """Return the bilingual labels and framework clause for one control."""
    source = control_register().get(control_id)
    if source is None:
        return {
            "name_en": control_id,
            "name_ar": control_id,
            "framework_clause": "",
            "domain_label_en": "",
            "domain_label_ar": "",
            "severity": "",
        }
    return {
        "name_en":          source.get("name_en", control_id),
        "name_ar":          source.get("name_ar", control_id),
        "framework_clause": source.get("framework_clause", ""),
        "domain_label_en":  source.get("domain_label_en", ""),
        "domain_label_ar":  source.get("domain_label_ar", ""),
        "severity":         source.get("severity", ""),
    }
