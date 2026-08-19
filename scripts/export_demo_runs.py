#!/usr/bin/env python3
"""Record real evaluation runs and export them for the interface to replay.

The deployed interface is a static build with no engine behind it. Rather
than invent a demonstration, this script runs the actual adaptive engine
against the actual probe corpus, once per (use case, submission profile)
pair, and writes what happened to a JSON file the interface replays step by
step.

Nothing in the output is written by hand. Each step carries the probe, the
model response, the scorer, the score and the evidence hash the run
produced. The verdict, the stopping reason and the per-control decision
bases are the engine's own.

Usage:
    uv run python scripts/export_demo_runs.py

Output:
    web/src/data/recorded_runs.json

Re-run it after any change to the engine, the corpus or the control
register, so the replay and the live path cannot drift apart.

British English throughout.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

_OUT = _REPO_ROOT / "web" / "src" / "data" / "recorded_runs.json"
_SAMPLES = _REPO_ROOT / "web" / "public" / "samples"

# Cap the response text carried into the interface. The whole exchange stays
# in the evidence table; the replay shows the opening of it and states the
# hash, which is what a reader checks.
_RESPONSE_CHARS = 600

def submissions() -> list[dict]:
    """Read the sample submissions the interface offers for upload.

    Recording the runs from the same files a reader downloads means the
    replay shows exactly what that file does, including the effect of a thin
    model card on the controls decided by attestation.
    """
    out = []
    for path in sorted(_SAMPLES.glob("*.mizan.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        out.append({
            "submission_id": path.name.replace(".mizan.json", ""),
            "name_en":       record.get("name_en", path.stem),
            "name_ar":       record.get("name_ar", ""),
            "provider":      record.get("provider", ""),
            "version":       record.get("version", ""),
            "profile":       record.get("evaluation_profile", "compliant"),
            "model_card":    record.get("model_card", {}),
        })
    return out


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _prepare_db() -> Path:
    """Create a throwaway database with the real schema."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="mizan-export-"))
    db = tmp_dir / "export.db"
    os.environ["MIZAN_DATABASE_URL"] = f"sqlite+aiosqlite:///{db}"
    ddl = (_REPO_ROOT / "engine" / "db" / "schema.sql").read_text(encoding="utf-8")
    conn = sqlite3.connect(str(db))
    conn.executescript(ddl)
    conn.commit()
    conn.close()
    return db


def _seed_rows(db: Path, model_id: str, use_case, evaluation_id: str, submission: dict) -> None:
    from mizan.api import catalogue

    now = _now()
    register = catalogue.control_register()
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT OR IGNORE INTO models (id, name_en, name_ar, provider, version, "
        "model_card, status, submitted_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            model_id,
            submission["name_en"],
            submission["name_ar"] or submission["name_en"],
            submission["provider"] or "MIZAN recording",
            submission["version"] or "1.0.0",
            json.dumps({"mizan_evaluation_profile": submission["profile"]}, ensure_ascii=False),
            "in_evaluation",
            now,
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO use_cases (id, name_en, name_ar, description_en, "
        "description_ar, use_case_class, confidence_threshold, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (
            use_case["id"], use_case["name_en"], use_case["name_ar"],
            use_case["description_en"], use_case["description_ar"],
            use_case["use_case_class"], float(use_case["confidence_threshold"]), now,
        ),
    )
    for control in register.values():
        conn.execute(
            "INSERT OR IGNORE INTO controls (id, use_case_id, name_en, name_ar, "
            "description_en, description_ar, framework_clause, is_mandatory, weight, "
            "suite_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                control["id"], use_case["id"], control["name_en"], control["name_ar"],
                control["description_en"], control["description_ar"],
                control.get("framework_clause", "MIZAN-CTL"), 1,
                control.get("weight", 1.0), control["suite_id"], now,
            ),
        )
    conn.execute(
        "INSERT INTO evaluations (id, model_id, use_case_id, status, arm_pulls, "
        "engine_config, started_at) VALUES (?,?,?,?,?,?,?)",
        (evaluation_id, model_id, use_case["id"], "running", "[]", "{}", now),
    )
    conn.commit()
    conn.close()


def record_run(db: Path, use_case_id: str, submission: dict) -> dict:
    """Run the engine once and return the recorded trace."""
    from mizan.agents.harness.adapters import MockEndpoint
    from mizan.agents.harness.batch_runner import BatchSuiteRunner
    from mizan.api import catalogue, certificate as certificate_issuer
    from mizan.engine.bandit.allocator import BanditEngine

    profile = submission["profile"]
    use_case = catalogue.use_case(use_case_id)
    if use_case is None:
        raise SystemExit(f"Unknown use case: {use_case_id}")

    controls = catalogue.engine_controls(use_case_id)
    mandatory_ids = {c["control_id"] for c in controls if c["is_mandatory"]}

    model_id = str(uuid.uuid4())
    evaluation_id = str(uuid.uuid4())
    _seed_rows(db, model_id, use_case, evaluation_id, submission)

    model_card = submission["model_card"]

    runner = BatchSuiteRunner(
        endpoint=MockEndpoint(profile=profile, seed=42),
        evaluation_id=evaluation_id,
        locale="en",
        mandatory_control_ids=mandatory_ids,
        model_card=model_card,
    )

    steps: list[dict] = []

    class Recorder:
        def __call__(self, suite_id: str, control_ids: list[str]) -> list[dict]:
            results = runner(suite_id, control_ids)
            if not results:
                return results
            first = results[0]
            row = _read_evidence(db, evaluation_id, first["probe_id"])
            payload = row.get("payload", {}) if row else {}
            steps.append({
                "step":         len(steps) + 1,
                "suite_id":     suite_id,
                "control_id":   first["control_id"],
                "probe_id":     first["probe_id"],
                "passed":       bool(first["passed"]),
                "score":        round(float(first["score"]), 4),
                "locale":       payload.get("locale", "en"),
                "prompt":       payload.get("prompt", "")[:_RESPONSE_CHARS],
                "response":     payload.get("response", "")[:_RESPONSE_CHARS],
                "scorer":       payload.get("scorer", ""),
                "evidence_type": payload.get("evidence_type", "probe_result"),
                "payload_hash": row.get("payload_hash", "") if row else "",
            })
            return results

    engine = BanditEngine(
        evaluation_id=evaluation_id,
        use_case_class=use_case["use_case_class"],
        confidence_threshold=float(use_case["confidence_threshold"]),
        controls=controls,
        engine_config={"random_seed": 42},
    )

    arm_pulls, stopping_reason, verdict = engine.run_sync(Recorder())
    control_decisions = engine.control_states()

    certificate = certificate_issuer.issue(
        evaluation_id=evaluation_id,
        model_id=model_id,
        use_case_id=use_case_id,
        verdict=verdict,
        control_decisions=control_decisions,
        stopping_reason=stopping_reason,
        total_queries=len(steps),
        evaluation_profile=profile,
        endpoint_url=None,
    )

    return {
        "run_id":            f"{use_case_id}-{submission['submission_id']}",
        "submission_id":     submission["submission_id"],
        "submission_name_en": submission["name_en"],
        "submission_name_ar": submission["name_ar"],
        "provider":          submission["provider"],
        "version":           submission["version"],
        "use_case_id":       use_case_id,
        "profile":           profile,
        "verdict":           verdict,
        "stopping_reason":   stopping_reason,
        "total_queries":     len(steps),
        "arm_pull_count":    len(arm_pulls),
        "steps":             steps,
        "control_decisions": control_decisions,
        "certificate":       certificate,
    }


def _read_evidence(db: Path, evaluation_id: str, probe_id: str) -> dict:
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT payload, payload_hash FROM evidence "
        "WHERE evaluation_id = ? AND probe_id = ? ORDER BY rowid DESC LIMIT 1",
        (evaluation_id, probe_id),
    ).fetchone()
    conn.close()
    if row is None:
        return {}
    try:
        payload = json.loads(row["payload"])
    except (json.JSONDecodeError, TypeError):
        payload = {}
    return {"payload": payload, "payload_hash": row["payload_hash"]}


def main() -> int:
    db = _prepare_db()
    from mizan.api import bindings, catalogue

    runs = []
    prepared = submissions()
    if not prepared:
        raise SystemExit(f"No sample submissions found in {_SAMPLES}")
    for use_case in catalogue.use_cases():
        for submission in prepared:
            run = record_run(db, use_case["id"], submission)
            runs.append(run)
            print(
                f"[recorded] {run['run_id']:<58} {run['verdict']:<9} "
                f"{run['stopping_reason']:<24} {run['total_queries']} probes"
            )

    document = {
        "generated_at":  _now(),
        "generated_by":  "scripts/export_demo_runs.py",
        "note": (
            "Recorded runs of the MIZAN adaptive engine against the offline "
            "probe corpus, using the deterministic mock adapter. The interface "
            "replays these when no engine is reachable. Every step, verdict and "
            "hash below was produced by the engine, not written by hand."
        ),
        "submissions":   [
            {k: v for k, v in s.items() if k != "model_card"} for s in prepared
        ],
        "use_cases":     catalogue.use_cases(),
        "controls":      list(catalogue.control_register().values()),
        "datasets":      bindings.dataset_bindings(),
        "runs":          runs,
    }

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
    size_kb = _OUT.stat().st_size / 1024
    print(f"Wrote {_OUT.relative_to(_REPO_ROOT)} ({size_kb:.0f} kB, {len(runs)} runs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
