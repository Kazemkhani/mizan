"""Certificate issuance.

An evaluation that reaches a verdict issues a certificate. The certificate
is assembled here from four sources, none of which is written by hand at
issuance time:

    the evaluation           verdict, stopping reason, probes conducted
    the control register     bilingual control names and framework clauses
    the engine control state per-control decision, basis and achieved bound
    the evidence table       the bundle hash the certificate is anchored to

The wording of the certificate, in both languages, comes from
suites/controls/certificate_content.json, which is the governance-owned
source for what the certificate asserts and what it declines to assert.

Two registers, as that document requires: a control decided by a confidence
bound and a control decided at budget exhaustion carry different basis
labels, and the achieved lower bound is printed for both. A pass that was
not statistically demonstrated says so on its face.

Signing: SOVEREIGN-TODO D-006. Until a real key is wired, the signature is a
labelled HMAC-SHA256 development stub over the evidence bundle hash, and the
certificate says so in its signature block rather than implying a sovereign
signature exists.

British English throughout.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from mizan.api import bindings, catalogue, store
from mizan.engine.db.database import evidence_bundle_hash

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CERT_CONTENT = _REPO_ROOT / "suites" / "controls" / "certificate_content.json"

# Development signing key. Labelled as a stub on the certificate face.
_STUB_KEY = b"mizan-development-signing-stub"

# A control decided by one of these bases was decided by statistical
# evidence; anything else was decided at budget exhaustion or by
# documentary attestation. certificate_content.json calls this the
# two-register rule.
_STATISTICAL_BASES = frozenset({
    "statistical_pass",
    "statistical_fail",
    "zero_violation_fail",
    "clean_run_bounded",
})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@lru_cache(maxsize=1)
def certificate_content() -> dict[str, Any]:
    """Return the governance-owned certificate wording."""
    return json.loads(_CERT_CONTENT.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _control_set_version() -> str:
    catalogue_file = _REPO_ROOT / "suites" / "controls" / "controls.json"
    data = json.loads(catalogue_file.read_text(encoding="utf-8"))
    return str(data.get("control_set_id", "unknown"))


def basis_labels(basis: str | None) -> dict[str, str]:
    """Return the bilingual display labels for one decision basis."""
    if basis is None:
        return {
            "label_en": "Not decided",
            "label_ar": "لم يُبتّ فيه",
            "register": "secondary",
        }
    definitions = certificate_content().get("decision_basis_register", {}).get(
        "basis_definitions", {}
    )
    record = definitions.get(basis, {})
    return {
        "label_en": record.get("label_en", basis.replace("_", " ").title()),
        "label_ar": record.get("label_ar", basis),
        "register": record.get("register", "secondary"),
    }


def _control_results(control_decisions: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the per-control results table."""
    rows: list[dict[str, Any]] = []
    for control_id, state in control_decisions.items():
        labels = catalogue.control_labels(control_id)
        basis = state.get("decision_basis")
        rows.append({
            "control_id":         control_id,
            "name_en":            labels["name_en"],
            "name_ar":            labels["name_ar"],
            "domain_label_en":    labels["domain_label_en"],
            "domain_label_ar":    labels["domain_label_ar"],
            "framework_clause":   labels["framework_clause"],
            "severity":           labels["severity"],
            "is_mandatory":       bool(state.get("is_mandatory", True)),
            "decision":           state.get("decision"),
            "decision_basis":     basis,
            "basis_labels":       basis_labels(basis),
            "statistically_decided": basis in _STATISTICAL_BASES,
            "probes_conducted":   int(state.get("n", 0)),
            "probes_passed":      int(state.get("s", 0)),
            "required_pass_rate": state.get("required_pass_rate"),
            "achieved_pass_rate_lower_bound": state.get("achieved_pass_rate_lower_bound"),
            "violation_rate_bound": state.get("violation_rate_bound"),
        })
    rows.sort(key=lambda r: (not r["is_mandatory"], r["control_id"]))
    return rows


def _evidence_hashes(evaluation_id: str) -> list[str]:
    rows = store.query(
        "SELECT payload_hash FROM evidence WHERE evaluation_id = ?",
        (evaluation_id,),
    )
    return [r["payload_hash"] for r in rows]


def issue(
    evaluation_id: str,
    model_id: str,
    use_case_id: str,
    verdict: str,
    control_decisions: dict[str, Any],
    stopping_reason: str | None,
    total_queries: int,
    evaluation_profile: str,
    endpoint_url: str | None,
) -> dict[str, Any]:
    """Assemble, store, and return one certificate record.

    Returns the stored record. Issuance is idempotent per evaluation: the
    certificates table carries a unique index on evaluation_id, so a second
    call for the same evaluation returns the certificate already issued.
    """
    existing = store.query_one(
        "SELECT * FROM certificates WHERE evaluation_id = ?", (evaluation_id,)
    )
    if existing is not None:
        return _row_to_record(existing)

    content = certificate_content()
    use_case = catalogue.use_case(use_case_id) or {}
    model = store.query_one("SELECT * FROM models WHERE id = ?", (model_id,)) or {}

    results = _control_results(control_decisions)
    mandatory = [r for r in results if r["is_mandatory"]]
    statistically_decided = [r for r in mandatory if r["statistically_decided"]]
    undecided = [r for r in mandatory if r["decision_basis"] is None]

    # Statistical tier only when every mandatory control earned a bound. A
    # control decided at budget exhaustion, and a control the corpus ran out
    # on before any bound could be asserted, both put the certificate in the
    # budget tier, whose wording states the shortfall.
    tier = (
        "statistical"
        if mandatory and len(statistically_decided) == len(mandatory)
        else "budget"
    )

    bundle_hash = evidence_bundle_hash(_evidence_hashes(evaluation_id))
    signature = hmac.new(_STUB_KEY, bundle_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    assertions = content.get("verdict_assertions", {}).get(verdict, {})
    body_key = f"body_{tier}_tier"

    certificate_data: dict[str, Any] = {
        "schema_version":     content.get("schema_version", "1.1"),
        "title_en":           content.get("certificate_title", {}).get("en", ""),
        "title_ar":           content.get("certificate_title", {}).get("ar", ""),
        "issuing_authority_en": content.get("issuing_authority", {}).get("en", ""),
        "issuing_authority_ar": content.get("issuing_authority", {}).get("ar", ""),
        "verdict":            verdict,
        "headline_en":        assertions.get("headline_en", verdict.upper()),
        "headline_ar":        assertions.get("headline_ar", ""),
        "body_en":            assertions.get(f"{body_key}_en", ""),
        "body_ar":            assertions.get(f"{body_key}_ar", ""),
        "evidence_tier":      tier,
        "model": {
            "id":        model_id,
            "name_en":   model.get("name_en", ""),
            "name_ar":   model.get("name_ar", ""),
            "provider":  model.get("provider", ""),
            "version":   model.get("version", ""),
        },
        "use_case": {
            "id":         use_case_id,
            "name_en":    use_case.get("name_en", ""),
            "name_ar":    use_case.get("name_ar", ""),
            "confidence_threshold": use_case.get("confidence_threshold"),
        },
        "control_set_version": _control_set_version(),
        "control_results":     results,
        "mandatory_controls":  len(mandatory),
        "controls_statistically_decided": len(statistically_decided),
        "controls_budget_decided": len(mandatory) - len(statistically_decided) - len(undecided),
        "controls_undecided":  len(undecided),
        "probes_conducted":    total_queries,
        "stopping_reason":     stopping_reason,
        "datasets_consulted":  bindings.bindings_for(use_case_id),
        "evaluation_served_by": (
            {"kind": "endpoint", "detail": endpoint_url}
            if endpoint_url
            else {"kind": "deterministic_mock", "detail": evaluation_profile}
        ),
        "validity_en":         content.get("validity_statement", {}).get("en", ""),
        "validity_ar":         content.get("validity_statement", {}).get("ar", ""),
        "asserts_en":          content.get("what_the_certificate_asserts", {}).get("en", []),
        "asserts_ar":          content.get("what_the_certificate_asserts", {}).get("ar", []),
        "does_not_assert_en":  content.get("what_the_certificate_does_not_assert", {}).get("en", []),
        "does_not_assert_ar":  content.get("what_the_certificate_does_not_assert", {}).get("ar", []),
        "signature_note_en": (
            "Development signing stub, HMAC-SHA256 over the evidence bundle hash. "
            "SOVEREIGN-TODO D-006: the sovereign signing key is not yet wired, so "
            "this signature verifies issuance by this installation only."
        ),
        "signature_note_ar": (
            "توقيع تطويري مؤقت بخوارزمية HMAC-SHA256 على بصمة حزمة الأدلة. "
            "لم يُربط مفتاح التوقيع السيادي بعد، ولذلك يُثبت هذا التوقيع الإصدار من هذا التركيب فقط."
        ),
    }

    certificate_id = str(uuid.uuid4())
    issued_at = _now()

    store.execute(
        """
        INSERT INTO certificates
            (id, evaluation_id, model_id, use_case_id, verdict,
             evidence_bundle_hash, certificate_data, signature, issued_at, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            certificate_id,
            evaluation_id,
            model_id,
            use_case_id,
            verdict,
            bundle_hash,
            json.dumps(certificate_data, ensure_ascii=False),
            signature,
            issued_at,
            None,
        ),
    )

    row = store.query_one("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
    return _row_to_record(row or {})


def _row_to_record(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a certificates row into the API response shape."""
    try:
        data = json.loads(row.get("certificate_data") or "{}")
    except (json.JSONDecodeError, TypeError):
        data = {}
    return {
        "id":                   row.get("id", ""),
        "evaluation_id":        row.get("evaluation_id", ""),
        "model_id":             row.get("model_id", ""),
        "use_case_id":          row.get("use_case_id", ""),
        "verdict":              row.get("verdict", "rejected"),
        "evidence_bundle_hash": row.get("evidence_bundle_hash", ""),
        "certificate_data":     data,
        "signature":            row.get("signature"),
        "issued_at":            row.get("issued_at", ""),
        "pdf_path":             row.get("pdf_path"),
    }
