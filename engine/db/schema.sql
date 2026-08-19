-- MIZAN Sovereign AI Model Registry
-- Schema v0.2.0  --  Wave 0 Foundation, F0-01 remediation
--
-- IMMUTABILITY MODEL
-- Two layers of enforcement, each independent:
--
--   Layer 1: Database triggers (this file).
--     evidence: BEFORE INSERT validates payload_hash format and hash chain.
--               BEFORE UPDATE and BEFORE DELETE raise and abort unconditionally.
--     certificates: BEFORE UPDATE allows only pdf_path and signature to be set
--                   after initial issuance; blocks changes to all identity and
--                   verdict fields. BEFORE DELETE raises and aborts.
--     An agent who reads only the application code will still hit the trigger.
--
--   Layer 2: Application layer (mizan/engine/db/database.py).
--     No UPDATE or DELETE is issued against evidence or the identity fields of
--     certificates. This is a second line of defence, not the first.
--
-- HASH CHAIN
--   Every evidence row carries chain_prev_hash, which is the payload_hash of
--   the immediately preceding evidence row for the same evaluation (empty
--   string for the genesis row). This creates a single-linked-list chain per
--   evaluation. Any deletion or excision breaks the chain at the next row.
--   scripts/verify_evidence.py traverses and audits the chain independently
--   of the triggers.
--   Trust boundary note: a party with write access to the database file can
--   drop the triggers, edit rows, and recompute a self-consistent chain. The
--   chain raises the cost of undetected tampering significantly; it does not
--   eliminate it. See docs/DECISIONS.md D-014 for the next step.
--
-- POSTGRES EQUIVALENTS
--   This file targets SQLite. Every SQLite-specific construct is accompanied
--   by a comment giving the Postgres equivalent. A ministry deploying on
--   Postgres should run the Postgres DDL (marked POSTGRES:) rather than this
--   file. SOVEREIGN-TODO: generate the Postgres DDL as a separate file in Wave 3.
--
-- DESIGN PRINCIPLES
--   1. Every table is Postgres-compatible. SQLite-specific types are avoided.
--      The only SQLite concession is the use of TEXT for UUID columns; in
--      Postgres these become UUID. A comment marks each such column.
--   2. Bilingual content uses explicit _en/_ar column pairs. This is
--      preferred over a locale-keyed JSON column because it makes SQL
--      queries explicit and avoids silent key-miss errors. JSONB is the
--      Postgres migration path if a third language is ever required.
--   3. The evidence table is append-only and content-addressed. Every row
--      carries a SHA-256 hash of its payload and a back-reference to the
--      preceding row's hash. Immutability is enforced by triggers.
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
--
-- IMMUTABILITY: enforced by trg_evidence_no_update and trg_evidence_no_delete
-- below. The triggers unconditionally RAISE(ABORT, ...) on any UPDATE or
-- DELETE. An application bug or a careless query will hit this and stop.
--
-- CONTENT-ADDRESSING: payload_hash is SHA-256 of payload (UTF-8). The
-- format is validated by trg_evidence_insert_validate. The value is
-- verified against the stored payload by scripts/verify_evidence.py.
-- SQLite has no built-in SHA-256 function, so the value itself cannot be
-- computed in a trigger; format validation (length = 64) is the database
-- check. Application-layer enforcement and the verify script provide the
-- cryptographic guarantee.
-- POSTGRES: Use a generated column:
--   payload_hash TEXT GENERATED ALWAYS AS
--     (encode(sha256(payload::bytea), 'hex')) STORED
-- and add a CHECK (payload_hash ~ '^[0-9a-f]{64}$').
--
-- HASH CHAIN: chain_prev_hash is the payload_hash of the immediately
-- preceding evidence row for the same evaluation. The first row carries
-- an empty string (the genesis sentinel). The chain is enforced by
-- trg_evidence_insert_validate:
--   - A genesis row (chain_prev_hash = '') is only allowed if no evidence
--     rows exist yet for this evaluation.
--   - A non-genesis row must reference an existing payload_hash for the
--     same evaluation.
-- Traversing the chain detects any deletion or excision; see
-- scripts/verify_evidence.py for the audit procedure.
-- POSTGRES: Add a trigger function performing the same checks.
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
    -- Must be exactly 64 lowercase hex characters. See column comment above.
    payload_hash    TEXT    NOT NULL,
    -- Back-reference to the payload_hash of the preceding evidence row for
    -- this evaluation (empty string for the genesis row). Forms a linked list
    -- that makes deletion and excision detectable without trusting the database.
    chain_prev_hash TEXT    NOT NULL DEFAULT '',
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
-- CONCURRENT-FORK GUARD: each (evaluation_id, chain_prev_hash) pair may appear
-- only once. This prevents two concurrent append_evidence() callers from both
-- reading the same tail hash and inserting two successor rows (forking the chain).
-- The first INSERT wins; the second receives a UNIQUE constraint error and must
-- retry. The genesis invariant (chain_prev_hash = '') is enforced by the same
-- index: there can be at most one genesis row per evaluation.
-- POSTGRES: CREATE UNIQUE INDEX idx_evidence_chain ON evidence(evaluation_id, chain_prev_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_chain
    ON evidence(evaluation_id, chain_prev_hash);

-- ------------------------------------------------------------
-- evidence BEFORE INSERT: validate payload_hash format and hash chain.
-- Three consecutive SELECT CASE statements run in order; the first
-- failing RAISE(ABORT, ...) stops execution.
-- POSTGRES: Replace with a PL/pgSQL trigger function checking the same
-- conditions; attach it with CREATE TRIGGER ... BEFORE INSERT ON evidence.
-- ------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_evidence_insert_validate
BEFORE INSERT ON evidence
BEGIN
    -- 1. payload_hash must be exactly 64 characters.
    --    SQLite cannot compute SHA-256, so the cryptographic value is
    --    verified by scripts/verify_evidence.py at every audit gate.
    --    This check catches obviously malformed values at the DB layer.
    SELECT CASE
        WHEN LENGTH(NEW.payload_hash) != 64
        THEN RAISE(ABORT, 'evidence.payload_hash must be 64 characters (SHA-256 hex)')
    END;
    -- 2. Genesis rows (chain_prev_hash = '') must be the first row for
    --    their evaluation. A second genesis row would fork the chain.
    SELECT CASE
        WHEN NEW.chain_prev_hash = '' AND EXISTS (
            SELECT 1 FROM evidence WHERE evaluation_id = NEW.evaluation_id
        )
        THEN RAISE(ABORT, 'evidence: chain_prev_hash may be empty only for the first row of an evaluation')
    END;
    -- 3. Non-genesis rows must reference an existing payload_hash for
    --    the same evaluation. An orphan reference would break the chain.
    SELECT CASE
        WHEN NEW.chain_prev_hash != '' AND NOT EXISTS (
            SELECT 1 FROM evidence
            WHERE payload_hash    = NEW.chain_prev_hash
              AND evaluation_id   = NEW.evaluation_id
        )
        THEN RAISE(ABORT, 'evidence: chain_prev_hash does not reference an existing payload_hash in the same evaluation')
    END;
END;

-- ------------------------------------------------------------
-- evidence BEFORE UPDATE: unconditional abort.
-- Applies to every UPDATE regardless of which columns are targeted.
-- POSTGRES: CREATE RULE evidence_no_update AS ON UPDATE TO evidence DO INSTEAD
--   NOTHING; -- or a trigger raising an exception. Also: REVOKE UPDATE ON
--   evidence FROM <application_role>; to block at the privilege layer.
-- ------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_evidence_no_update
BEFORE UPDATE ON evidence
BEGIN
    SELECT RAISE(ABORT, 'evidence is append-only: UPDATE is prohibited by charter');
END;

-- ------------------------------------------------------------
-- evidence BEFORE DELETE: unconditional abort.
-- POSTGRES: CREATE RULE evidence_no_delete AS ON DELETE TO evidence DO INSTEAD
--   NOTHING; -- or a trigger raising an exception. Also: REVOKE DELETE ON
--   evidence FROM <application_role>;
-- ------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_evidence_no_delete
BEFORE DELETE ON evidence
BEGIN
    SELECT RAISE(ABORT, 'evidence is append-only: DELETE is prohibited by charter');
END;


-- ============================================================
-- certificates
-- Issued on evaluation completion. References an evidence bundle
-- hash so the certificate can be verified independently of the
-- database. The bundle hash is SHA-256 of the concatenation of all
-- payload_hash values for the evaluation, sorted lexicographically.
--
-- IMMUTABILITY STATE MACHINE:
--   Certificates are written once, at evaluation completion. The core
--   identity and verdict fields are immutable from that point. Two fields
--   may be updated after issuance:
--     pdf_path  -- set when the PDF renderer writes the file (Wave 3).
--     signature -- set when the signing key is wired (Wave 3).
--   All other fields are blocked by trg_certificates_no_update.
--   DELETE is unconditionally blocked by trg_certificates_no_delete.
--
-- POSTGRES: Implement the same logic as a PL/pgSQL BEFORE UPDATE trigger.
--   Also REVOKE DELETE ON certificates FROM <application_role>.
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
    -- MAY be updated after issuance (see immutability state machine above).
    signature               TEXT,
    -- Postgres: TIMESTAMPTZ
    issued_at               TEXT    NOT NULL,
    -- Filesystem path to the generated PDF, relative to the repo root.
    -- NULL until the PDF renderer writes it (Wave 3).
    -- MAY be updated after issuance (see immutability state machine above).
    pdf_path                TEXT,

    CONSTRAINT certificates_verdict_values
        CHECK (verdict IN ('certified', 'rejected'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_certificates_evaluation
    ON certificates(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_certificates_model
    ON certificates(model_id);

-- ------------------------------------------------------------
-- certificates BEFORE UPDATE: block changes to identity and verdict fields.
-- Allowed: pdf_path and signature (set post-issuance in Wave 3).
-- Blocked: all other columns.
-- POSTGRES: PL/pgSQL trigger raising an exception when any protected
--   column changes. Use NEW.<col> IS DISTINCT FROM OLD.<col> for
--   NULL-safe comparison.
-- ------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_certificates_no_update
BEFORE UPDATE ON certificates
BEGIN
    SELECT CASE
        WHEN OLD.evaluation_id        != NEW.evaluation_id
          OR OLD.model_id             != NEW.model_id
          OR OLD.use_case_id          != NEW.use_case_id
          OR OLD.verdict              != NEW.verdict
          OR OLD.evidence_bundle_hash != NEW.evidence_bundle_hash
          OR OLD.certificate_data     != NEW.certificate_data
          OR OLD.issued_at            != NEW.issued_at
        THEN RAISE(ABORT,
            'certificates: identity and verdict fields are immutable after issuance; only pdf_path and signature may be updated')
    END;
END;

-- ------------------------------------------------------------
-- certificates BEFORE DELETE: unconditional abort.
-- POSTGRES: CREATE RULE certificates_no_delete AS ON DELETE TO certificates
--   DO INSTEAD NOTHING; -- or a trigger raising an exception.
--   Also: REVOKE DELETE ON certificates FROM <application_role>;
-- ------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_certificates_no_delete
BEFORE DELETE ON certificates
BEGIN
    SELECT RAISE(ABORT, 'certificates may not be deleted');
END;


-- ============================================================
-- engine_memory
-- Persists learnt suite orderings per use-case class so the Monte
-- Carlo Strategy Search layer can retrieve faster test orderings
-- on subsequent evaluations. Keyed on use_case_class.
-- ============================================================
CREATE TABLE IF NOT EXISTS engine_memory (
    -- Postgres: BIGINT GENERATED ALWAYS AS IDENTITY
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
