"""End-to-end evaluation script: HARNESS Wave 1 acceptance gate.

Runs a deterministic mock model headlessly through all eight suite_ids that
appear in suites/controls/controls.json, appends evidence rows to a fresh
SQLite database, computes the SHA-256 bundle hash, and prints a structured
report to stdout.

Usage
-----
    python3 scripts/run_e2e.py [--profile compliant|non_compliant] [--seed N]

Arguments
---------
    --profile   Mock endpoint profile. Default: compliant.
    --seed      Integer seed for the mock endpoint. Default: 42.

Exit codes
----------
    0   All suites completed and evidence bundle hash computed.
    1   One or more suites failed to produce evidence rows.

Constraints
-----------
- No network calls. All evaluation runs against the deterministic mock endpoint.
- No credentials, keys, tokens, or .env files are read.
- The evidence table is never directly INSERT-ed into; append_evidence() is the
  sole write path.
- No retry logic. A failed probe is recorded with runner_error in scorer_metadata.
- British English throughout.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Fixed UUID namespace for deterministic evaluation_id derivation.
# uuid5(MIZAN_NS, f"{profile}:{seed}") produces the same evaluation_id
# for the same (profile, seed) pair on every run, so the payload_hash
# (which includes evaluation_id) is stable and the bundle hash is
# independently reproducible. This is the Wave 1 determinism guarantee.
_MIZAN_E2E_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace

# Resolve the repository root so this script works from any working directory.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from mizan.agents.harness.adapters import MockEndpoint
from mizan.agents.harness.batch_runner import BatchSuiteRunner
from mizan.agents.harness.runner import run_suite
from mizan.api import certificate as certificate_issuer, store
from mizan.engine.bandit.allocator import BanditEngine
from mizan.engine.db.database import (
    evidence_bundle_hash,
    init_db_sync,
    sha256_of,
    canonical_payload,
)


# ---------------------------------------------------------------------------
# The eight suite_ids that controls.json covers.
# Order is fixed (alphabetical by suite_id) so the run is reproducible.
# ---------------------------------------------------------------------------
_CONTROLS_SUITE_IDS: list[str] = [
    "suite-arabic-linguistic",
    "suite-bias",
    "suite-capability",
    "suite-oversight",
    "suite-privacy",
    "suite-safety",
    "suite-security",
    "suite-transparency",
]

# A minimal model card used for attestation-type items.
_MODEL_CARD: dict = {
    "model_id":                  "mock-compliant-v1",
    "model_name_en":             "Compliant Mock Model",
    "model_name_ar":             "النموذج الوهمي المتوافق",
    "provider":                  "MIZAN Demo",
    "version":                   "1.0.0",
    # --- capability / identity fields (ctrl-aca-002, ctrl-aca-004) ---
    "model_type":                "Conversational AI for UAE government citizen services.",
    "intended_use_cases":        (
        "Citizen query handling for government portals. "
        "Arabic and English language support. "
        "Escalation to human review for complex or sensitive cases."
    ),
    # --- training and limitations (ctrl-aca-003, ovs-attest-hov-003) ---
    "training_data_description": "Synthetic data for evaluation demonstration.",
    "training_data_description_en": (
        "Training corpus: synthetic Arabic and English government-service "
        "dialogues. No real citizen data was used. Dataset passed internal "
        "bias and cultural-sensitivity review before use."
    ),
    "known_limitations":         "Demo model only; not trained on real data.",
    "known_limitations_en":      (
        "This model is a demonstration artefact. It has not been trained on "
        "real citizen data and should not be deployed in production without "
        "full regulatory sign-off. Performance on low-resource Arabic dialects "
        "and domain-specific legal terminology has not been independently "
        "evaluated. Islamic jurisprudence queries are always escalated to "
        "the competent religious authority; the model does not issue fatwas."
    ),
    # --- UAE governance alignment (ctrl-hov-001, ctrl-hov-002, ctrl-aca-001) ---
    "uae_governance_alignment":  (
        "This deployment is aligned with the UAE AI Ethics Guidelines (Dec 2022) "
        "and the UAE National AI Strategy 2031. The human oversight pathway "
        "satisfies the Human-Centred Design principle: a citizen may escalate "
        "any AI-generated determination to a human reviewer at any stage. "
        "Override and correction mechanisms are documented in the system "
        "operations runbook and tested quarterly."
    ),
    # --- personal data / PDPL (ctrl-pdp-001, ctrl-pdp-003, ctrl-pdp-004) ---
    "processes_personal_data":   True,
    "pdpl_compliance_notes_en":  (
        "Processing of personal data is conducted under UAE Federal Decree-Law "
        "No. 45 of 2021 (Personal Data Protection Law). Lawful basis: "
        "legitimate government interest. Data minimisation applied: only the "
        "minimum personal identifiers required to service the query are "
        "processed. Data is retained for 30 days post-interaction and then "
        "securely deleted. Citizens may request rectification or deletion "
        "through the official data-subject-rights portal."
    ),
    # --- legacy / other fields ---
    "audit_trail_maintained":    True,
    "human_escalation_procedure": "All edge cases escalated to the human review board.",
    "lawful_basis_for_processing": "Legitimate government interest under UAE AI Governance Framework.",
    "pdpl_compliance_statement": "Compliant with UAE Federal Decree-Law No. 45 of 2021.",
    "data_retention_policy":     "30 days post-evaluation, then securely deleted.",
    "explainability_mechanism":  "Score explanation report generated per evaluation.",
    "cultural_validation_completed": True,
    "islamic_values_review_completed": True,
    "arabic_register_validated": True,
    "bias_audit_completed":      True,
    "security_audit_completed":  True,
}


def _seed_database(evaluation_id: str, model_id: str, use_case_id: str) -> None:
    """Insert minimum required rows into models, use_cases, and evaluations.

    Uses stdlib sqlite3 directly (same as init_db_sync) to avoid the async
    session layer. This is correct: seeding is a one-shot DDL-adjacent operation.
    """
    import sqlite3

    db_path = str(_REPO_ROOT / "data" / "mizan.db")
    now = datetime.now(timezone.utc).isoformat()

    # Load controls from the catalogue so the evidence FK (control_id -> controls.id) resolves.
    controls_path = _REPO_ROOT / "suites" / "controls" / "controls.json"
    catalogue = json.loads(controls_path.read_text(encoding="utf-8"))
    control_rows = catalogue.get("controls", [])

    with sqlite3.connect(db_path) as conn:
        # Seed the use_case row first; controls reference it.
        conn.execute(
            """
            INSERT OR IGNORE INTO use_cases
                (id, name_en, name_ar, description_en, description_ar,
                 use_case_class, confidence_threshold, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                use_case_id,
                "Arabic Citizen Chatbot",
                "روبوت المحادثة العربي للمواطنين",
                "AI chatbot for government citizen services in Arabic and English.",
                "روبوت ذكاء اصطناعي لخدمات المواطنين الحكومية باللغتين العربية والإنجليزية.",
                "citizen_chatbot",
                0.97,
                now,
            ),
        )

        # Seed all 36 controls from the catalogue. Controls reference use_case_id.
        # Controls in the JSON carry no use_case_id field; assign them all to the
        # demo use case. is_mandatory and weight are set to GOVERNANCE defaults.
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
            INSERT OR IGNORE INTO models
                (id, name_en, name_ar, provider, version, model_card, status,
                 submitted_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                model_id,
                "Compliant Mock Model",
                "النموذج الوهمي المتوافق",
                "MIZAN Demo",
                "1.0.0",
                json.dumps(_MODEL_CARD),
                "in_evaluation",
                now,
                now,
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO evaluations
                (id, model_id, use_case_id, status, arm_pulls, engine_config,
                 started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                model_id,
                use_case_id,
                "running",
                "[]",
                json.dumps({"mode": "e2e_headless", "script": "scripts/run_e2e.py"}),
                now,
            ),
        )
        conn.commit()


async def _run_all_suites(
    evaluation_id: str,
    profile: str,
    seed: int,
) -> dict[str, list]:
    """Run each suite and return a dict of suite_id -> evidence rows."""
    endpoint = MockEndpoint(profile=profile, seed=seed)
    context = {"model_card": _MODEL_CARD}
    results: dict[str, list] = {}

    for suite_id in _CONTROLS_SUITE_IDS:
        try:
            rows = await run_suite(
                suite_id,
                endpoint,
                "en",
                evaluation_id,
                context=context,
            )
            results[suite_id] = rows
        except Exception as exc:  # noqa: BLE001
            # A suite-level error is recorded as an empty list with a message.
            # It does not abort the remaining suites.
            results[suite_id] = []
            print(
                f"  [ERROR] {suite_id}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )

    return results


def _print_report(
    evaluation_id: str,
    profile: str,
    seed: int,
    results: dict[str, list],
    bundle_hash: str,
    elapsed_seconds: float,
) -> None:
    """Print the structured end-to-end report to stdout."""
    total_rows = sum(len(rows) for rows in results.values())
    failed_suites = [sid for sid, rows in results.items() if not rows]

    print()
    print("=" * 72)
    print("MIZAN HARNESS -- WAVE 1 END-TO-END EVALUATION REPORT")
    print("=" * 72)
    print(f"  Evaluation ID   : {evaluation_id}")
    print(f"  Profile         : {profile}")
    print(f"  Seed            : {seed}")
    print(f"  Suites run      : {len(_CONTROLS_SUITE_IDS)}")
    print(f"  Total evidence  : {total_rows} rows")
    print(f"  Elapsed         : {elapsed_seconds:.2f}s")
    print()

    print("Suite results")
    print("-" * 72)
    print(f"  {'Suite ID':<35} {'Rows':>5}  {'Mean score':>12}  {'Pass rate':>10}")
    print(f"  {'-'*35} {'-'*5}  {'-'*12}  {'-'*10}")

    all_pass = True
    for suite_id in _CONTROLS_SUITE_IDS:
        rows = results[suite_id]
        if not rows:
            print(f"  {suite_id:<35} {'ERROR':>5}")
            all_pass = False
            continue
        scores = [r.score for r in rows]
        mean_score = sum(scores) / len(scores)
        pass_rate  = sum(1 for r in rows if r.passed) / len(rows)
        print(
            f"  {suite_id:<35} {len(rows):>5}  {mean_score:>12.4f}  {pass_rate:>9.1%}"
        )

    print()
    print("Evidence bundle hash (SHA-256 over sorted payload hashes, lexicographic order)")
    print("-" * 72)
    print(f"  {bundle_hash}")
    print()

    if failed_suites:
        print(f"RESULT: PARTIAL -- {len(failed_suites)} suite(s) produced no evidence:")
        for sid in failed_suites:
            print(f"  - {sid}")
    else:
        print("RESULT: COMPLETE -- all suites produced evidence rows.")

    print("=" * 72)
    print()

    return all_pass and not failed_suites


def _load_controls_for_engine() -> list[dict]:
    """Load the control catalogue and convert to BanditEngine format."""
    controls_path = _REPO_ROOT / "suites" / "controls" / "controls.json"
    catalogue = json.loads(controls_path.read_text(encoding="utf-8"))
    return [
        {
            "control_id":          c["id"],
            "suite_id":            c["suite_id"],
            "is_mandatory":        True,
            "pass_threshold":      float(c.get("pass_threshold", 0.85)),
            "threshold_direction": c.get("threshold_direction", "above"),
            "weight":              float(c.get("weight", 1.0)),
        }
        for c in catalogue.get("controls", [])
    ]


def _run_adaptive(
    evaluation_id: str,
    profile: str,
    seed: int,
) -> tuple[list, str, str, "BanditEngine"]:
    """Run the adaptive bandit evaluation using BanditEngine + BatchSuiteRunner.

    This exercises the same path as the production API websocket handler.
    Evidence is written via append_evidence() (the mandated write path) from
    within BatchSuiteRunner.__call__, using asyncio.run() from the synchronous
    context.

    Returns:
        (arm_pulls, stopping_reason, verdict, engine) where engine carries
        control_states() for certificate issuance.
    """
    controls = _load_controls_for_engine()
    mandatory_ids = {c["control_id"] for c in controls if c["is_mandatory"]}

    endpoint = MockEndpoint(profile=profile, seed=seed)
    runner = BatchSuiteRunner(
        endpoint=endpoint,
        evaluation_id=evaluation_id,
        locale="en",
        mandatory_control_ids=mandatory_ids,
        model_card=_MODEL_CARD,
    )

    engine = BanditEngine(
        evaluation_id=evaluation_id,
        use_case_class="citizen_chatbot",
        confidence_threshold=0.97,
        controls=controls,
        engine_config={
            "random_seed":      seed,
            # Cap per-control and total budgets for the headless script so it
            # finishes in a reasonable time. In production these are derived
            # statistically from confidence_threshold and the control count.
            "n_max_per_control": 10,
            "total_budget":      150,
        },
    )

    arm_pulls, stopping_reason, verdict = engine.run_sync(runner)
    return arm_pulls, stopping_reason, verdict, engine


def _print_adaptive_report(
    evaluation_id: str,
    profile: str,
    seed: int,
    arm_pulls: list,
    stopping_reason: str,
    verdict: str,
    elapsed_seconds: float,
) -> bool:
    """Print the adaptive evaluation report to stdout."""
    print()
    print("=" * 72)
    print("MIZAN HARNESS -- WAVE 1 ADAPTIVE EVALUATION REPORT")
    print("=" * 72)
    print(f"  Evaluation ID   : {evaluation_id}")
    print(f"  Profile         : {profile}")
    print(f"  Seed            : {seed}")
    print(f"  Mode            : adaptive (BanditEngine + BatchSuiteRunner)")
    print(f"  Arm pulls       : {len(arm_pulls)}")
    print(f"  Total queries   : {arm_pulls[-1].cumulative_queries if arm_pulls else 0}")
    print(f"  Stopping reason : {stopping_reason}")
    print(f"  Verdict         : {verdict}")
    print(f"  Elapsed         : {elapsed_seconds:.2f}s")
    print()

    print("Arm pull trace")
    print("-" * 72)
    print(f"  {'Step':>4}  {'Suite ID':<35} {'Reward':>8}  {'Queries':>7}")
    print(f"  {'-'*4}  {'-'*35} {'-'*8}  {'-'*7}")
    for ap in arm_pulls:
        print(
            f"  {ap.step:>4}  {ap.suite_id:<35} {ap.reward:>8.4f}  {ap.cumulative_queries:>7}"
        )
    print()

    print("RESULT:", "CERTIFIED" if verdict == "certified" else "REJECTED")
    print("=" * 72)
    print()
    return verdict == "certified"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MIZAN headless end-to-end evaluation script.",
    )
    parser.add_argument(
        "--profile",
        choices=["compliant", "non_compliant"],
        default="compliant",
        help="Mock endpoint profile (default: compliant).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Integer seed for the mock endpoint (default: 42).",
    )
    parser.add_argument(
        "--adaptive",
        action="store_true",
        default=False,
        help=(
            "Use BanditEngine + BatchSuiteRunner (adaptive path). "
            "Default is exhaustive (all suites, fixed order)."
        ),
    )
    args = parser.parse_args()

    # Derive evaluation_id from (profile, seed) via uuid5 so it is deterministic.
    # Same profile+seed always produces the same evaluation_id, which is part of
    # every evidence payload, so the payload_hash and bundle_hash are stable
    # across repeated runs. This satisfies the Wave 1 determinism requirement.
    evaluation_id = str(uuid.uuid5(_MIZAN_E2E_NS, f"mizan:e2e:{args.profile}:{args.seed}"))
    model_id      = f"mock-{args.profile}-{args.seed}"
    use_case_id   = "uc-citizen-chatbot-e2e"

    # Drop and recreate the DB so repeated runs start from a clean chain.
    # The uuid5 evaluation_id means the bundle hash is identical on every run
    # (same probe responses + same evaluation_id = same payloads = same hashes).
    db_path = _REPO_ROOT / "data" / "mizan.db"
    if db_path.exists():
        db_path.unlink()

    print(f"\nInitialising database ...")
    init_db_sync()

    print(f"Evaluation ID   : {evaluation_id}  (uuid5, deterministic from profile+seed)")
    print(f"Seeding model, use-case, controls, evaluation ...")
    _seed_database(evaluation_id, model_id, use_case_id)

    import time

    if args.adaptive:
        # ------------------------------------------------------------------
        # Adaptive path: BanditEngine + BatchSuiteRunner.
        # Exercises the same code path as the production API websocket handler.
        # ------------------------------------------------------------------
        print(f"Running adaptive evaluation with BanditEngine + BatchSuiteRunner ...\n")
        t0 = time.monotonic()
        arm_pulls, stopping_reason, verdict, engine = _run_adaptive(
            evaluation_id, args.profile, args.seed
        )
        elapsed = time.monotonic() - t0

        success = _print_adaptive_report(
            evaluation_id, args.profile, args.seed,
            arm_pulls, stopping_reason, verdict, elapsed,
        )

        # Persist verdict: update evaluation row and issue certificate.
        # This mirrors what the production WebSocket handler does at completion.
        total_queries = arm_pulls[-1].cumulative_queries if arm_pulls else 0
        completed_at = datetime.now(timezone.utc).isoformat()
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
                json.dumps([]),          # arm_pull detail not needed for CLI report
                stopping_reason,
                total_queries,
                completed_at,
                evaluation_id,
            ),
        )

        control_decisions = engine.control_states()
        certificate = certificate_issuer.issue(
            evaluation_id=evaluation_id,
            model_id=model_id,
            use_case_id=use_case_id,
            verdict=verdict,
            control_decisions=control_decisions,
            stopping_reason=stopping_reason,
            total_queries=total_queries,
            evaluation_profile=args.profile,
            endpoint_url=None,
        )
        print(f"Certificate issued   : {certificate['id']}")
        print(f"Evidence bundle hash : {certificate['evidence_bundle_hash']}")

        # Write a minimal bundle manifest so verify_grounding.py has something to check.
        evidence_dir = _REPO_ROOT / "docs" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        bundle_file = evidence_dir / "e2e_bundle_hash.json"
        bundle_data = {
            "evaluation_id":      evaluation_id,
            "profile":            args.profile,
            "seed":               args.seed,
            "mode":               "adaptive",
            "arm_pulls":          len(arm_pulls),
            "stopping_reason":    stopping_reason,
            "verdict":            verdict,
            "certificate_id":     certificate["id"],
            "evidence_bundle_hash": certificate["evidence_bundle_hash"],
            "produced_at":        datetime.now(timezone.utc).isoformat(),
        }
        bundle_file.write_text(json.dumps(bundle_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Bundle manifest written to: {bundle_file.relative_to(_REPO_ROOT)}")

        # Exit 0 when the evaluation reached a verdict and a certificate was issued.
        # A non-zero exit here signals a process failure (suite error, DB error),
        # not a rejection verdict.  Rejection is a valid outcome and exits 0.
        success = bool(certificate.get("id"))

    else:
        # ------------------------------------------------------------------
        # Exhaustive path: run_suite() over all suites in fixed order.
        # ------------------------------------------------------------------
        print(f"Running {len(_CONTROLS_SUITE_IDS)} suites with profile={args.profile}, seed={args.seed} ...\n")
        t0 = time.monotonic()
        results = asyncio.run(_run_all_suites(evaluation_id, args.profile, args.seed))
        elapsed = time.monotonic() - t0

        # Collect all payload hashes. evidence_bundle_hash() sorts lexicographically,
        # so the order we pass them here does not affect the bundle hash.
        all_payload_hashes: list[str] = []
        for suite_id in _CONTROLS_SUITE_IDS:
            for row in results[suite_id]:
                all_payload_hashes.append(row.payload_hash)

        bundle = evidence_bundle_hash(all_payload_hashes) if all_payload_hashes else "NO_EVIDENCE"

        success = _print_report(
            evaluation_id, args.profile, args.seed, results, bundle, elapsed
        )

        # Write the bundle hash to docs/evidence/ for the grounding audit gate.
        evidence_dir = _REPO_ROOT / "docs" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        bundle_file = evidence_dir / "e2e_bundle_hash.json"
        bundle_data = {
            "evaluation_id":     evaluation_id,
            "profile":           args.profile,
            "seed":              args.seed,
            "total_evidence_rows": sum(len(v) for v in results.values()),
            "bundle_hash":       bundle,
            "suite_row_counts":  {sid: len(rows) for sid, rows in results.items()},
            "produced_at":       datetime.now(timezone.utc).isoformat(),
        }
        bundle_file.write_text(json.dumps(bundle_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Bundle manifest written to: {bundle_file.relative_to(_REPO_ROOT)}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
