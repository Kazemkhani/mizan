# MIZAN Architecture

Sovereign AI Model Registry and Adaptive Compliance Engine.
Version 0.1.0, Wave 0 Foundation.

> **Read [`docs/FLOW.md`](FLOW.md) first** if you want to understand what
> runs in what order. This document covers the schema, module boundaries,
> and interface contracts. FLOW.md covers the evaluation sequence, how
> UCB1 and MCSS compose, and the integration gap at the suite-runner
> boundary.

---

## 1. System overview

MIZAN adjudicates AI models against a defined set of government controls
and issues cryptographically signed bilingual certificates. The system
comprises four bounded layers:

```
Web shell (React, Vite, TypeScript)
    |  WebSocket + HTTP
API layer (FastAPI, Pydantic v2)
    |  Python function calls
Evaluation engine (UCB1 bandit, MCSS, suite runners)
    |  SQLAlchemy Core
Database (SQLite for demo; Postgres-ready DDL)
```

All four layers share a single schema, a single evidence model, and a
single certificate format. There is no separate analytics database.

---

## 2. Directory structure

```
mizan/                     Python package (importable as "mizan")
  engine/
    db/
      database.py          Engine initialisation, session factory,
                           SHA-256 content-addressing utilities
      __init__.py
    bandit/                UCB1 allocator (BANDIT, Wave 1)
    mcss/                  Monte Carlo Strategy Search (BANDIT, Wave 1)
  agents/
    harness/               Suite runners and model adapters (HARNESS, Wave 1)
    redteam/               Red-team probe engine (SENTINEL, Wave 1)
  api/
    main.py                FastAPI application, lifespan, CORS
    schemas.py             All Pydantic request/response models
    routes/
      health.py            GET /api/v1/health
      models_route.py      POST, GET /api/v1/models[/{id}]
      use_cases_route.py   GET /api/v1/use-cases[/{id}]
      evaluations_route.py POST, GET /api/v1/evaluations[/{id}]
      evidence_route.py    GET /api/v1/evidence/{hash}, GET /api/v1/evidence
      certificates_route.py GET /api/v1/certificates[/{id}]
      websocket_route.py   WS /api/v1/ws/evaluations/{id}/stream

engine/                    Non-Python assets
  db/
    schema.sql             DDL: all tables, indices, constraints

agents/                    Stub directory (HARNESS/SENTINEL populate in Wave 1)
suites/                    Suite definitions (GOVERNANCE/RASHID populate in Wave 1)
  controls/
scripts/
  seed.py                  Deterministic demo data seeder
  reset.py                 Database reset and re-seed
  audit/
    register_lint.py       Register discipline linter (British English, no em-dashes)
tests/
  test_health.py           Wave 0 acceptance tests (8 tests)
web/
  src/
    main.tsx               Entry point; imports ATELIER tokens.css and base.css
    App.tsx                Application root and I18nProvider
    i18n/
      index.tsx            I18n context, useTranslation hook
      en.ts                English (en-GB) string catalogue
      ar.ts                Arabic (ar-AE) string catalogue
    components/
      LanguageToggle.tsx   Language switch button
    styles/
      tokens.css           ATELIER design tokens (ATELIER owns)
      base.css             ATELIER base stylesheet (ATELIER owns)
docs/
  CHARTER.md               Project charter
  DELIVERY_PLAN.md         Wave schedule and acceptance criteria
  ARCHITECTURE.md          This document
  DECISIONS.md             Consequential design decisions and rationale
  audit/                   AUDITOR signoff files (per wave)
  evidence/                Reproducible measurement outputs
  reports/                 Agent completion reports (per agent per wave)
  submission/              Final pitch artefacts (Wave 4)
```

---

## 3. Data model

All tables are defined in `engine/db/schema.sql`. Every column is
documented there with an inline comment. This section provides the
higher-level design rationale.

### 3.1 models

Records an AI model submitted for evaluation. Status progresses through:
`pending -> in_evaluation -> certified | rejected`.

Bilingual fields: `name_en`, `name_ar`. The `model_card` column holds
a JSON object conforming to the model card schema (section 5 below).

### 3.2 use_cases

Government use-case categories that drive control selection. Each use
case defines a `confidence_threshold` in [0, 1]: the minimum confidence
the bandit engine must reach across all mandatory controls before a
CERTIFIED verdict can be issued.

The `use_case_class` column is the key used by the MCSS memory layer to
retrieve learnt suite orderings from `engine_memory`.

Bilingual fields: `name_en`, `name_ar`, `description_en`, `description_ar`.

Five use cases seeded in Wave 0:

| ID | Name (English) | use_case_class | Confidence threshold |
|----|----------------|----------------|---------------------|
| uc-001 | Citizen-Facing Arabic Chatbot | citizen_chatbot | 0.97 |
| uc-002 | Internal Document Summarisation | document_summarisation | 0.90 |
| uc-003 | Benefits Eligibility Triage | benefits_triage | 0.98 |
| uc-004 | Traffic Incident Classification | incident_classification | 0.95 |
| uc-005 | Procurement Document Analysis | procurement_analysis | 0.92 |

### 3.3 controls

Individual compliance controls. Each control belongs to exactly one use
case, references one test suite, and carries a `framework_clause` mapping
it to the UAE AI Governance Framework.

Controls that MIZAN defines (not directly enumerated in a published UAE
Framework clause) carry a `MIZAN-CTL-NNN` identifier and are labelled
explicitly in certificate output. This is required by the charter to avoid
inventing unmapped controls.

`is_mandatory` (0 or 1): mandatory controls gate the verdict; advisory
controls contribute to the score only.

Bilingual fields: `name_en`, `name_ar`, `description_en`, `description_ar`.

### 3.4 evaluations

One row per (model, use_case) pair per evaluation run.

The `arm_pulls` column holds the complete adjudication trail as a JSON
array. Each element conforms to the `ArmPull` Pydantic schema:

```json
{
  "step": 1,
  "suite_id": "suite-arabic-safety",
  "arm_index": 0,
  "reward": 0.87,
  "ucb_value": 1.12,
  "posterior_state": {
    "suite-arabic-safety": {
      "pulls": 5,
      "total_reward": 4.35,
      "mean_reward": 0.87
    }
  },
  "cumulative_queries": 5
}
```

The `engine_config` column holds a JSON snapshot of the bandit
configuration at the time of the evaluation. This ensures results are
reproducible even if the default configuration changes.

### 3.5 evidence (append-only, content-addressed)

One row per probe result. The `payload` column holds the full
probe-and-response record as JSON (schema in section 6).

`payload_hash` is the SHA-256 hex digest of `payload` (UTF-8 encoded).
This is the content address: a consumer may re-hash the payload and
compare to `payload_hash` to verify the record has not been altered.

**No UPDATE or DELETE is ever issued against this table.** The data
access layer (`database.py`) must enforce this. The database schema
defines no triggers for this because SQLite trigger semantics differ from
Postgres; enforcement is at the application layer in Wave 1.

Uniqueness: `payload_hash` has a UNIQUE index. If two probes produce
identical payloads (e.g., in deterministic mock mode), the second insert
must generate a modified payload with a distinguishing field rather than
violating the constraint.

### 3.6 certificates

Issued once per completed evaluation. References `evaluation_id`,
`model_id`, and `use_case_id` by foreign key.

The `evidence_bundle_hash` is computed as:
```
SHA-256(sort(payload_hashes).join(""))
```
where `payload_hashes` is the list of all `evidence.payload_hash` values
for the evaluation, sorted lexicographically. This is deterministic and
independent of insertion order. A verifier can reproduce it from the
evidence records without trusting the `certificates` row.

The `signature` column holds a cryptographic signature over
`evidence_bundle_hash`. In Wave 0 this is a stub (SOVEREIGN-TODO: D-006).
In Wave 3 it will be an HMAC-SHA256 under a key stored in the deployment
secrets.

`certificate_data` holds the full structured certificate payload as JSON.
Its schema is specified in section 7.

### 3.7 engine_memory

Persists the UCB1 posterior state and MCSS suite ordering for each
use-case class. This is the mechanism by which the registry compounds:
each completed evaluation updates the memory for its use-case class, and
subsequent evaluations of the same class start with a better arm ordering,
reaching the stopping criterion faster.

`use_case_class` is the lookup key. It must match `use_cases.use_case_class`
exactly.

`suite_ordering`: JSON array of suite IDs in learnt descending order of
expected information gain.

`arm_statistics`: JSON object mapping suite_id to posterior statistics
used by the UCB1 formula.

`total_evaluations`: monotonically increasing count of completed evaluations
that contributed to this memory row.

---

## 4. Bandit engine interface contract (for BANDIT, Wave 1)

BANDIT owns `mizan/engine/bandit/` and `mizan/engine/mcss/`.

**Required inputs:**

- `evaluation_id: str` -- the evaluation record to update
- `use_case_id: str` -- determines which controls and confidence threshold apply
- `engine_config: dict` -- bandit hyperparameters (UCB1 exploration constant,
  budget per arm, Hoeffding delta, etc.)

**Required outputs per step:**

- An `ArmPull` object (Pydantic schema in `mizan/api/schemas.py`) emitted
  to the WebSocket streaming route as a `StreamEvent(event_type="arm_pull")`.
- After each probe: an `EvidenceRow` emitted as a
  `StreamEvent(event_type="probe_result")`.

**Stopping:**

The engine must write a `stopping_reason` string to `evaluations.stopping_reason`
and set `evaluations.status` to "completed" and `evaluations.verdict` to
"certified" or "rejected" before emitting the final `stop` event.

Allowed stopping reasons:
- `hoeffding_bound_met` -- sufficient confidence on all mandatory controls
- `mandatory_control_failed` -- a mandatory control failed with high confidence
- `budget_exhausted` -- total query budget reached without a conclusive verdict

**Memory update:**

On completion, BANDIT must write or update the `engine_memory` row for
the evaluation's `use_case_class` using the posterior state from the final
`arm_pulls` entry.

**Determinism:**

The engine must accept a `random_seed` key in `engine_config`. Under a
fixed seed, results must be exactly reproducible (required for
`scripts/prove_reduction.py`).

---

## 5. Model card schema

Defined as the `ModelCard` Pydantic model in `mizan/api/schemas.py`.
Extended from Mitchell et al. 2019 with UAE governance and PDPL fields.

GOVERNANCE (Wave 1) expands the `uae_governance_alignment` sub-object to
cover all nine UAE AI Governance Framework principles. The field names
established in Wave 0 must not be renamed.

---

## 6. Evidence payload schema

One evidence payload covers one probe. JSON structure:

```json
{
  "probe_id": "safety-ar-001",
  "suite_id": "suite-arabic-safety",
  "control_id": "ctrl-001-001",
  "locale": "ar",
  "prompt": "...",
  "response": "...",
  "scorer": "keyword_blocklist_v1",
  "score": 0.0,
  "passed": false,
  "scorer_metadata": {}
}
```

The `payload_hash` stored in the `evidence` row is SHA-256 of the
JSON-serialised form of this object (UTF-8, keys sorted).

---

## 7. Certificate data schema

The `certificate_data` JSON object in the `certificates` row:

```json
{
  "certificate_id": "...",
  "version": "1.0",
  "model": { "id": "...", "name_en": "...", "name_ar": "..." },
  "use_case": { "id": "...", "name_en": "...", "name_ar": "..." },
  "verdict": "certified",
  "verdict_ar": "معتمد",
  "issued_at": "...",
  "evidence_bundle_hash": "...",
  "controls": [
    {
      "control_id": "ctrl-001-001",
      "name_en": "...",
      "name_ar": "...",
      "framework_clause": "...",
      "is_mandatory": true,
      "score": 0.94,
      "passed": true,
      "evidence_hash": "..."
    }
  ],
  "evaluator": "MIZAN v0.1.0",
  "signature": "..."
}
```

GOVERNANCE and RASHID (Wave 1) define the bilingual content of the
certificate PDF. The JSON schema above is fixed.

---

## 8. API contracts

Base URL: `/api/v1`

| Method | Path | Request schema | Response schema |
|--------|------|---------------|-----------------|
| GET | /health | -- | HealthOut |
| POST | /models | ModelIn | ModelOut (201) |
| GET | /models | -- | list[ModelRow] |
| GET | /models/{id} | -- | ModelOut |
| GET | /use-cases | -- | list[UseCaseRow] |
| GET | /use-cases/{id} | -- | UseCaseDetail |
| POST | /evaluations | EvaluationIn | EvaluationOut (202) |
| GET | /evaluations | model_id (query, optional) | list[EvaluationRow] |
| GET | /evaluations/{id} | -- | EvaluationOut |
| GET | /evidence/{hash} | -- | EvidenceRow |
| GET | /evidence | evaluation_id (query, required) | list[EvidenceRow] |
| GET | /certificates/{id} | -- | CertificateOut |
| GET | /certificates | model_id (query, optional) | list[CertificateOut] |
| WS | /ws/evaluations/{id}/stream | -- | StreamEvent (streaming) |

All Pydantic schemas are defined in `mizan/api/schemas.py`. Field names
and types are frozen from Wave 0. Changes require updating ARCHITECTURE.md
and a DECISIONS.md entry.

---

## 9. i18n contract (for RASHID, Wave 1)

The i18n module is at `web/src/i18n/index.tsx`.

RASHID's responsibility:
- Review and correct every string in `web/src/i18n/ar.ts` to formal Gulf
  governmental register. Strings marked `[REVIEW]` require particular attention.
- Do not rename keys. Do not add keys in `ar.ts` without a matching key in `en.ts`.
- All Arabic content must be RTL-correct. The `dir` attribute is managed by
  `I18nProvider`; no additional dir-setting is required in individual components.

The `useTranslation()` hook returns:
```typescript
{
  t: (key: string) => string,   // translates key using active locale
  locale: 'en' | 'ar',
  setLocale: (locale: 'en' | 'ar') => void,
  dir: 'ltr' | 'rtl',
}
```

---

## 10. WebSocket streaming contract (for HARNESS, Wave 1; ATELIER, Wave 3)

Endpoint: `WS /api/v1/ws/evaluations/{evaluation_id}/stream`

Events conform to `StreamEvent` in `mizan/api/schemas.py`:

```typescript
{
  event_type: "arm_pull" | "probe_result" | "stop" | "error",
  evaluation_id: string,
  payload: object,   // ArmPull | partial EvidenceRow | EvaluationRow | error
  sequence: number,
  timestamp: string,
}
```

HARNESS wires the real engine output to this WebSocket in Wave 1.
ATELIER consumes it in the live evaluation theatre in Wave 3.
The contract (event_type values and payload shapes) is fixed.

---

## 11. Design decisions

See `docs/DECISIONS.md` for the full rationale of every consequential choice.
