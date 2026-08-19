"""Pydantic v2 request and response schemas for the MIZAN API.

Every route defined in mizan.api.routes uses these schemas as its
input and output contracts. Wave 1 workstreams must not change the
field names or types without a corresponding ARCHITECTURE.md update
and a migration note in DECISIONS.md.

Naming convention:
    <Resource>In    -- request body (input from caller)
    <Resource>Out   -- response body (output to caller)
    <Resource>Row   -- lightweight list-item representation
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared value types
# ---------------------------------------------------------------------------

ModelStatus = Literal["pending", "in_evaluation", "certified", "rejected"]
EvaluationStatus = Literal["pending", "running", "completed", "failed"]
Verdict = Literal["certified", "rejected"]

# Which deterministic mock adapter serves a submission that carries no live
# endpoint URL. The mock is the offline evaluation path by charter design
# (see mizan/agents/harness/adapters.py); the profile is declared by the
# submitter and is printed on the certificate face, so a reader can tell a
# mock-served evaluation from one served by a live endpoint.
EvaluationProfile = Literal["compliant", "non_compliant"]


# ---------------------------------------------------------------------------
# Model card schema
# Extended from Mitchell et al. 2019 with UAE governance and PDPL fields.
# Wave 1 (GOVERNANCE) will fill in the full field set; these are the
# mandatory fields Wave 0 establishes.
# ---------------------------------------------------------------------------

class ModelCard(BaseModel):
    """Structured model card conforming to Mitchell et al. 2019 extended with
    UAE AI Governance Framework and PDPL requirements."""

    # Core identification
    model_name_en: str = Field(..., description="Model name in English")
    model_name_ar: str = Field(..., description="Model name in Arabic")
    model_type: str = Field(..., description="Model architecture type, e.g. LLM, classifier")
    training_data_description_en: str = Field(..., description="Description of training data in English")
    training_data_description_ar: str = Field(..., description="Description of training data in Arabic")

    # UAE AI Governance Framework fields (GOVERNANCE populates in Wave 1)
    uae_governance_alignment: dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping from UAE AI Governance Framework principle to compliance evidence",
    )

    # PDPL fields (Personal Data Protection Law, UAE 2021)
    processes_personal_data: bool = Field(
        ...,
        description="Whether the model processes personal data as defined under UAE PDPL 2021",
    )
    pdpl_compliance_notes_en: str = Field(default="", description="PDPL compliance notes in English")
    pdpl_compliance_notes_ar: str = Field(default="", description="PDPL compliance notes in Arabic")

    # Intended use
    intended_use_cases: list[str] = Field(
        default_factory=list,
        description="List of use-case identifiers this model is intended for",
    )

    # Limitations and risks
    known_limitations_en: str = Field(default="", description="Known limitations in English")
    known_limitations_ar: str = Field(default="", description="Known limitations in Arabic")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ModelIn(BaseModel):
    """Request body for model registration (POST /api/v1/models)."""

    name_en: str = Field(..., min_length=1, max_length=256)
    name_ar: str = Field(..., min_length=1, max_length=256)
    provider: str = Field(..., min_length=1, max_length=128)
    version: str = Field(..., min_length=1, max_length=64)
    endpoint_url: str | None = Field(
        default=None,
        description="OpenAI-compatible endpoint URL. Omit to use the deterministic mock adapter.",
    )
    evaluation_profile: EvaluationProfile = Field(
        default="compliant",
        description=(
            "Which deterministic mock adapter serves this submission when no "
            "endpoint URL is given. Declared by the submitter and recorded on "
            "the certificate face."
        ),
    )
    model_card: ModelCard


class ModelOut(BaseModel):
    """Full model record returned after registration or lookup."""

    id: str
    name_en: str
    name_ar: str
    provider: str
    version: str
    endpoint_url: str | None
    evaluation_profile: EvaluationProfile = "compliant"
    model_card: dict[str, Any]
    status: ModelStatus
    submitted_at: str
    updated_at: str


class ModelRow(BaseModel):
    """Lightweight model record for list responses."""

    id: str
    name_en: str
    name_ar: str
    provider: str
    version: str
    status: ModelStatus
    submitted_at: str


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------

class UseCaseRow(BaseModel):
    """Use-case record for list responses (GET /api/v1/use-cases)."""

    id: str
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    use_case_class: str
    confidence_threshold: float


class ControlRow(BaseModel):
    """Control record nested within a use-case detail response."""

    id: str
    name_en: str
    name_ar: str
    framework_clause: str
    is_mandatory: bool
    weight: float
    suite_id: str


class UseCaseDetail(UseCaseRow):
    """Full use-case record including its controls."""

    controls: list[ControlRow] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evaluations
# ---------------------------------------------------------------------------

class EvaluationIn(BaseModel):
    """Request body for starting an evaluation (POST /api/v1/evaluations)."""

    model_id: str = Field(..., description="ID of the registered model to evaluate")
    use_case_id: str = Field(..., description="ID of the use case to evaluate against")
    engine_config_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional bandit configuration overrides. See docs/ARCHITECTURE.md section 4.",
    )


class ArmPull(BaseModel):
    """One step in the bandit adjudication trail."""

    step: int
    suite_id: str
    arm_index: int
    reward: float
    ucb_value: float
    # Posterior state snapshot: maps suite_id -> { pulls, total_reward, mean_reward }
    posterior_state: dict[str, Any]
    cumulative_queries: int


class EvaluationOut(BaseModel):
    """Full evaluation record including the adjudication trail."""

    id: str
    model_id: str
    use_case_id: str
    status: EvaluationStatus
    verdict: Verdict | None
    arm_pulls: list[ArmPull]
    stopping_reason: str | None
    total_queries: int
    engine_config: dict[str, Any]
    started_at: str
    completed_at: str | None
    # Per-control decision record produced by the bandit engine.
    # Keys are control_ids. Each value carries:
    #   decision (bool|null), basis (str, one of: statistical_pass,
    #   statistical_fail, zero_violation_fail, clean_run_bounded,
    #   budget_pass, budget_fail), n (int, probes conducted),
    #   violation_rate_bound (float|null, Clopper-Pearson upper bound
    #   for zero-tolerance controls after a clean run).
    # Certificate consumers must distinguish guaranteed from budget-limited
    # decisions via the basis field.
    control_decisions: dict[str, Any] = Field(default_factory=dict)


class EvaluationRow(BaseModel):
    """Lightweight evaluation record for list and status responses."""

    id: str
    model_id: str
    use_case_id: str
    status: EvaluationStatus
    verdict: Verdict | None
    total_queries: int
    started_at: str
    completed_at: str | None


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceRow(BaseModel):
    """Evidence record returned by hash lookup (GET /api/v1/evidence/{hash})."""

    id: str
    evaluation_id: str
    suite_id: str
    control_id: str
    probe_id: str
    # Full probe-and-response record as a structured object.
    payload: dict[str, Any]
    payload_hash: str
    score: float
    passed: bool
    collected_at: str


# ---------------------------------------------------------------------------
# Certificates
# ---------------------------------------------------------------------------

class CertificateOut(BaseModel):
    """Full certificate record (GET /api/v1/certificates/{id})."""

    id: str
    evaluation_id: str
    model_id: str
    use_case_id: str
    verdict: Verdict
    evidence_bundle_hash: str
    certificate_data: dict[str, Any]
    signature: str | None
    issued_at: str
    pdf_path: str | None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthOut(BaseModel):
    """Response from the health endpoint."""

    status: Literal["ok"] = "ok"
    version: str
    database: Literal["ok", "error"]


# ---------------------------------------------------------------------------
# WebSocket streaming
# ---------------------------------------------------------------------------

class StreamEvent(BaseModel):
    """One event emitted over the evaluation streaming WebSocket.

    event_type values:
        arm_pull      -- the bandit pulled an arm; payload is ArmPull
        probe_result  -- one probe completed; payload is EvidenceRow (partial)
        stop          -- evaluation concluded; payload is EvaluationRow
        error         -- unrecoverable error; payload has a 'message' key
    """

    event_type: Literal["arm_pull", "probe_result", "stop", "error"]
    evaluation_id: str
    payload: dict[str, Any]
    sequence: int
    timestamp: str
