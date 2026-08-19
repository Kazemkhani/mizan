-- MIZAN Sovereign AI Model Registry
-- Schema v0.1.0  --  Wave 0 Foundation
--
-- Design principles:
--   1. Every table is Postgres-compatible. SQLite-specific types are avoided.
--      The only SQLite concession is the use of TEXT for UUID columns; in
--      Postgres these become UUID. A comment marks each such column.
--   2. Bilingual content uses explicit _en/_ar column pairs. This is
--      preferred over a locale-keyed JSON column because it makes SQL
--      queries explicit and avoids silent key-miss errors. JSONB is the
--      Postgres migration path if a third language is ever required.
--   3. The evidence table is append-only and content-addressed. No UPDATE
--      or DELETE is ever issued against it. Every row carries a SHA-256
--      hash of its payload so the record is self-verifiable.
--   4. The evaluations table records the full adjudication trail: every
--      arm pull, the reward observed, the posterior state after each step,
--      and the stopping reason. Nothing is summarised away.
--   5. Timestamps are stored as ISO-8601 text in SQLite, as TIMESTAMPTZ
--      in Postgres (the comment marks the upgrade path).

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;


-- ============================================================
-- models
-- Registered AI models submitted for evaluation.
-- ============================================================
CREATE TABLE IF NOT EXISTS models (
    -- Postgres: UUID DEFAULT gen_random_uuid()
    id              TEXT        NOT NULL PRIMARY KEY,
    name_en         TEXT        NOT NULL,
    name_ar         TEXT        NOT NULL,
    provider        TEXT        NOT NULL,
    version         TEXT        NOT NULL,
    -- Optional HTTP endpoint conforming to the OpenAI-compatible interface.
    -- NULL when the model is evaluated via the deterministic mock adapter.
    endpoint_url    TEXT,
    -- JSON object conforming to the model card schema (docs/ARCHITECTURE.md
    -- section 5). Stored as TEXT in SQLite; use JSONB in Postgres.
    model_card      TEXT        NOT NULL DEFAULT '{}',
    -- Lifecycle state. Allowed values: pending, in_evaluation, certified, rejected.
    status          TEXT        NOT NULL DEFAULT 'pending',
    -- Postgres: TIMESTAMPTZ NOT NULL DEFAULT now()
    submitted_at    TEXT        NOT NULL,
    updated_at      TEXT        NOT NULL,

    CONSTRAINT models_status_values
        CHECK (status IN ('pending', 'in_evaluation', 'certified', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_models_status    ON models(status);
CREATE INDEX IF NOT EXISTS idx_models_provider  ON models(provider);


-- ============================================================
-- use_cases
-- Government use-case categories that drive control selection.
-- ============================================================
CREATE TABLE IF NOT EXISTS use_cases (
    id                  TEXT    NOT NULL PRIMARY KEY,
    name_en             TEXT    NOT NULL,
    name_ar             TEXT    NOT NULL,
    description_en      TEXT    NOT NULL,
    description_ar      TEXT    NOT NULL,
    -- MCSS memory lookup key. Identifies the use-case class so the bandit
    -- engine can retrieve previously learnt suite orderings.
    use_case_class      TEXT    NOT NULL,
    -- Minimum confidence required for a CERTIFIED verdict. Real in [0, 1].
    confidence_threshold REAL   NOT NULL DEFAULT 0.95,
    created_at          TEXT    NOT NULL,

    CONSTRAINT use_cases_threshold_range
        CHECK (confidence_threshold >= 0.0 AND confidence_threshold <= 1.0)
);


-- ============================================================
-- controls
-- Individual compliance controls mapped to the UAE AI Governance
-- Framework. Each control belongs to exactly one use case.
-- ============================================================
CREATE TABLE IF NOT EXISTS controls (
    id                  TEXT    NOT NULL PRIMARY KEY,
    use_case_id         TEXT    NOT NULL REFERENCES use_cases(id),
    name_en             TEXT    NOT NULL,
    name_ar             TEXT    NOT NULL,
    description_en      TEXT    NOT NULL,
    description_ar      TEXT    NOT NULL,
    -- Clause reference in the UAE AI Governance Framework, e.g.
    -- "Principle 3 - Transparency". Controls defined by MIZAN itself
    -- (not directly mapped to a published clause) carry the prefix
    -- "MIZAN-CTL-" and are labelled explicitly in certificate output.
    framework_clause    TEXT    NOT NULL,
    -- Mandatory controls must pass for certification. Advisory controls
    -- contribute to the overall score but do not gate the verdict.
    is_mandatory        INTEGER NOT NULL DEFAULT 1,
    -- Weight in [0, 1]. Mandatory controls typically carry weight >= 0.5.
    weight              REAL    NOT NULL DEFAULT 1.0,
    -- Which test suite covers this control. References a suite identifier
    -- defined in the suite catalogue (suites/controls/).
    suite_id            TEXT    NOT NULL,
    created_at          TEXT    NOT NULL,

    CONSTRAINT controls_mandatory_values
        CHECK (is_mandatory IN (0, 1)),
    CONSTRAINT controls_weight_range
        CHECK (weight >= 0.0 AND weight <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_controls_use_case ON controls(use_case_id);
CREATE INDEX IF NOT EXISTS idx_controls_suite    ON controls(suite_id);


-- ============================================================
-- evaluations
-- One evaluation record per (model, use_case) pair.
-- The arm_pulls column records the full adjudication trail as a
-- JSON array of objects:
--   { step, suite_id, arm_index, reward, ucb_value, posterior_state,
--     cumulative_queries }
-- This is the complete evidence of how the bandit engine reached its
-- decision; it is never summarised away.
-- ============================================================
CREATE TABLE IF NOT EXISTS evaluations (
    id              TEXT    NOT NULL PRIMARY KEY,
    model_id        TEXT    NOT NULL REFERENCES models(id),
    use_case_id     TEXT    NOT NULL REFERENCES use_cases(id),
    -- Lifecycle state. Allowed values: pending, running, completed, failed.
    status          TEXT    NOT NULL DEFAULT 'pending',
    -- Final verdict. NULL until evaluation completes.
    verdict         TEXT,
    -- JSON array. See column comment above.
    arm_pulls       TEXT    NOT NULL DEFAULT '[]',
    -- Human-readable reason the engine stopped: e.g. "hoeffding_bound_met",
    -- "budget_exhausted", "mandatory_control_failed".
    stopping_reason TEXT,
    -- Total number of probe queries issued across all suite arms.
    total_queries   INTEGER NOT NULL DEFAULT 0,
    -- JSON snapshot of the bandit configuration used for this evaluation,
    -- so results are reproducible even if configuration changes later.
    engine_config   TEXT    NOT NULL DEFAULT '{}',
    -- Postgres: TIMESTAMPTZ
    started_at      TEXT    NOT NULL,
    completed_at    TEXT,

    CONSTRAINT evaluations_status_values
        CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    CONSTRAINT evaluations_verdict_values
        CHECK (verdict IS NULL OR verdict IN ('certified', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_evaluations_model     ON evaluations(model_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_use_case  ON evaluations(use_case_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_status    ON evaluations(status);


-- ============================================================
-- evidence
-- Append-only. One row per probe result.
-- The payload column holds the full probe-and-response record as JSON.
-- payload_hash is SHA-256(payload). A consumer can re-hash the payload
-- and compare to payload_hash to verify the record has not been altered.
-- No UPDATE or DELETE is ever issued against this table; the application
-- layer must enforce this at the data access level.
-- ============================================================
CREATE TABLE IF NOT EXISTS evidence (
    id              TEXT    NOT NULL PRIMARY KEY,
    evaluation_id   TEXT    NOT NULL REFERENCES evaluations(id),
    -- Suite and control identifiers that this evidence record satisfies.
    suite_id        TEXT    NOT NULL,
    control_id      TEXT    NOT NULL REFERENCES controls(id),
    -- Individual probe identifier within the suite.
    probe_id        TEXT    NOT NULL,
    -- Full probe-and-response record as a JSON object. The schema is
    -- defined in docs/ARCHITECTURE.md section 6.
    payload         TEXT    NOT NULL,
    -- SHA-256 hex digest of payload (UTF-8 encoded). Content-addressed.
    payload_hash    TEXT    NOT NULL,
    -- Score in [0, 1] assigned by the suite scorer.
    score           REAL    NOT NULL,
    -- 1 if the probe passed the control threshold, 0 otherwise.
    passed          INTEGER NOT NULL,
    -- Postgres: TIMESTAMPTZ
    collected_at    TEXT    NOT NULL,

    CONSTRAINT evidence_score_range
        CHECK (score >= 0.0 AND score <= 1.0),
    CONSTRAINT evidence_passed_values
        CHECK (passed IN (0, 1))
);

-- payload_hash is the primary lookup key for evidence retrieval.
CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_hash         ON evidence(payload_hash);
CREATE        INDEX IF NOT EXISTS idx_evidence_evaluation   ON evidence(evaluation_id);
CREATE        INDEX IF NOT EXISTS idx_evidence_control      ON evidence(control_id);


-- ============================================================
-- certificates
-- Issued on evaluation completion. References an evidence bundle
-- hash so the certificate can be verified independently of the
-- database. The bundle hash is SHA-256 of the concatenation of all
-- payload_hash values for the evaluation, sorted lexicographically.
-- ============================================================
CREATE TABLE IF NOT EXISTS certificates (
    id                      TEXT    NOT NULL PRIMARY KEY,
    evaluation_id           TEXT    NOT NULL REFERENCES evaluations(id),
    model_id                TEXT    NOT NULL REFERENCES models(id),
    use_case_id             TEXT    NOT NULL REFERENCES use_cases(id),
    -- Final verdict: certified or rejected.
    verdict                 TEXT    NOT NULL,
    -- SHA-256 of all evidence payload_hashes for the evaluation,
    -- sorted lexicographically and concatenated, then hashed again.
    evidence_bundle_hash    TEXT    NOT NULL,
    -- Full certificate payload as a JSON object. Schema in
    -- docs/ARCHITECTURE.md section 7.
    certificate_data        TEXT    NOT NULL DEFAULT '{}',
    -- Cryptographic signature over evidence_bundle_hash.
    -- SOVEREIGN-TODO: wire the real signing key in Wave 3.
    -- Until then, a deterministic HMAC-SHA256 stub is used.
    signature               TEXT,
    -- Postgres: TIMESTAMPTZ
    issued_at               TEXT    NOT NULL,
    -- Filesystem path to the generated PDF, relative to the repo root.
    -- NULL until the PDF renderer writes it (Wave 3).
    pdf_path                TEXT,

    CONSTRAINT certificates_verdict_values
        CHECK (verdict IN ('certified', 'rejected'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_certificates_evaluation
    ON certificates(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_certificates_model
    ON certificates(model_id);


-- ============================================================
-- engine_memory
-- Persists learnt suite orderings per use-case class so the Monte
-- Carlo Strategy Search layer can retrieve faster test orderings
-- on subsequent evaluations. Keyed on use_case_class.
-- ============================================================
CREATE TABLE IF NOT EXISTS engine_memory (
    -- Postgres: SERIAL or BIGINT GENERATED ALWAYS AS IDENTITY
    id                  INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    -- The key used by MCSS to retrieve memory. Must match
    -- use_cases.use_case_class exactly.
    use_case_class      TEXT        NOT NULL UNIQUE,
    -- JSON array of suite arm identifiers in the learnt order.
    suite_ordering      TEXT        NOT NULL DEFAULT '[]',
    -- JSON object mapping suite_id -> { pulls, total_reward, mean_reward,
    -- confidence_bound }. The UCB1 posterior for each arm.
    arm_statistics      TEXT        NOT NULL DEFAULT '{}',
    -- Number of completed evaluations that contributed to this memory.
    total_evaluations   INTEGER     NOT NULL DEFAULT 0,
    -- Postgres: TIMESTAMPTZ
    updated_at          TEXT        NOT NULL
);
