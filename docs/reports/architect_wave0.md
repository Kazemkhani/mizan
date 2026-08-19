# ARCHITECT Wave 0 Completion Report

Wave 0 Foundation, MIZAN Sovereign AI Model Registry.
Author: ARCHITECT, Chief Systems Architect.
Date: 2026-08-19.

---

## 1. What was built

### Python toolchain

- `pyproject.toml` at repository root.
- Python 3.12 target (interpreter resolved from Homebrew Python 3.12.12).
- `uv sync` resolves 48 packages including: fastapi 0.141.1, uvicorn 0.52.4,
  pydantic 2.13.4, sqlalchemy 2.0.52, aiosqlite 0.22.1, numpy 2.5.2,
  matplotlib 3.11.1, weasyprint 69.0, cryptography 50.0.0, httpx 0.28.1,
  greenlet 3.5.5.
- Dev extras: pytest 9.1.1, pytest-asyncio 1.4.0, ruff 0.16.3.
- `uv run python -c "import mizan"` works.

### Data model

- DDL at `engine/db/schema.sql`.
- Seven tables: models, use_cases, controls, evaluations, evidence,
  certificates, engine_memory.
- All columns documented inline in the DDL.
- All constraints defined: CHECK on status enumerations, weight ranges,
  boolean fields; UNIQUE on evidence.payload_hash;
  UNIQUE on engine_memory.use_case_class; UNIQUE on certificates.evaluation_id.
- Bilingual fields implemented as `_en`/`_ar` column pairs throughout.
- Evidence table append-only by design; enforcement documented at application
  and schema levels.
- Certificate evidence_bundle_hash algorithm documented in ARCHITECTURE.md
  section 3.6.

### API layer

- FastAPI application at `mizan/api/main.py` with async lifespan (calls `init_db`).
- CORS configured for Vite dev server (port 5173).
- Docs at `/api/docs` (Swagger UI) and `/api/redoc`.
- Twelve routes across six route modules plus one WebSocket endpoint:
  health, models (3 routes), use-cases (2), evaluations (3), evidence (2),
  certificates (2), WebSocket (1).
- All routes have full Pydantic v2 request and response models.
- Handlers return fixture data in Wave 0; real DB calls are wired in Wave 1.
- WebSocket stub at `WS /api/v1/ws/evaluations/{id}/stream` emits three
  synthetic events to prove the contract and close cleanly.
- Five government use cases seeded as fixture data in the route handlers.

### Web shell

- React 18 + Vite 5 + TypeScript (strict mode, `noUnusedLocals`,
  `noUnusedParameters`).
- `web/src/main.tsx` imports ATELIER's `tokens.css` and `base.css`.
- i18n: `I18nProvider` and `useTranslation` hook in `web/src/i18n/index.tsx`.
  English and Arabic catalogues in `en.ts` and `ar.ts`.
- `I18nProvider` sets `document.documentElement.lang` and
  `document.documentElement.dir` on every locale change.
- `LanguageToggle` component toggles between `en` (LTR) and `ar` (RTL).
- TypeScript check (`npm run lint`): zero errors.
- ATELIER has delivered `tokens.css` and `base.css` concurrently.

### Scripts and Makefile

- `scripts/seed.py`: idempotent (INSERT OR IGNORE); seeds 5 use cases,
  8 models, 2 engine_memory rows.
- `scripts/reset.py`: deletes the SQLite file and re-initialises; supports
  `--no-seed` flag.
- `Makefile` targets: `dev` (parallel API + web), `api`, `web`, `test`,
  `seed`, `reset`, `lint`, `clean`, `demo` (stub), `prove` (stub).

### Documentation

- `docs/ARCHITECTURE.md`: schema documented table by table, API contracts
  tabulated, module boundaries defined, BANDIT/HARNESS/RASHID interface
  contracts specified explicitly.
- `docs/DECISIONS.md`: 10 decisions logged with alternatives and rationale.

---

## 2. Interface contracts Wave 1 must honour

### BANDIT (engine owner)

Write to `mizan/engine/bandit/` and `mizan/engine/mcss/`.

Required interface:
- Accept `evaluation_id`, `use_case_id`, `engine_config` as inputs.
- Emit `StreamEvent(event_type="arm_pull", payload=ArmPull.model_dump())`
  to the WebSocket route after each arm pull.
- Emit `StreamEvent(event_type="probe_result", payload=...)` after each probe.
- Emit `StreamEvent(event_type="stop", payload=EvaluationRow.model_dump())`
  on termination.
- Write the complete `arm_pulls` JSON array to `evaluations.arm_pulls`.
- Write `stopping_reason`, `status="completed"`, `verdict` to `evaluations`.
- Update `engine_memory` for the evaluation's `use_case_class`.
- Accept `engine_config["random_seed"]` and reproduce results deterministically.

Pydantic schemas to use: `ArmPull`, `EvaluationOut`, `StreamEvent`
(all in `mizan/api/schemas.py`).

Database access: use `mizan.engine.db.database.get_session()`.

### GOVERNANCE (controls owner)

Write to `suites/controls/`. Use the route fixture data in
`mizan/api/routes/use_cases_route.py` as the control schema reference.
Replace fixture data with real DB calls against `controls` and `use_cases`
tables. Do not change the `UseCaseDetail`, `ControlRow`, or `UseCaseRow`
Pydantic schemas.

The `framework_clause` field must map to a specific published UAE AI
Governance Framework clause or carry the prefix `MIZAN-CTL-` with explicit
labelling in certificate output.

### HARNESS (suite runner owner)

Write to `mizan/agents/harness/`.

Required interface:
- Runner function signature: `run_suite(suite_id, model_endpoint, locale) -> list[EvidenceRow]`.
- Each `EvidenceRow.payload_hash` must equal `sha256_of(json.dumps(payload, sort_keys=True))`.
  Use `mizan.engine.db.database.sha256_of()`.
- Evidence rows must be written to the `evidence` table (append-only).
- Never issue UPDATE or DELETE against the `evidence` table.
- Uniqueness constraint: if two probes produce identical payloads, add a
  distinguishing `_dedup` key to the payload before hashing.
- Provide a deterministic mock endpoint adapter for offline demo mode.

### RASHID (Arabic layer owner)

- Correct every Arabic string in `web/src/i18n/ar.ts` to formal Gulf
  governmental register. Strings marked `[REVIEW]` require particular
  attention. Do not rename keys.
- Provide Arabic-native (not translated) suite items for every suite in
  `suites/arabic/`.
- All Arabic content in certificates must be in Gulf governmental register.
- Do not add styles to `web/src/styles/tokens.css` or `web/src/styles/base.css`.

---

## 3. Decisions summary

| ID | Decision | Rationale |
|----|----------|-----------|
| D-001 | `mizan/` Python package at root | Avoids naming conflict with asset directories |
| D-002 | SQLAlchemy Core (not ORM) | Postgres-ready without ORM overhead |
| D-003 | `sqlite3.executescript()` for DDL | Handles semicolons in SQL comments |
| D-004 | `_en`/`_ar` column pairs | Explicit, fast, SQL-queryable |
| D-005 | WeasyPrint for PDF | Native RTL/Arabic via Pango; CSS reuse |
| D-006 | HMAC-SHA256 stub signature | PKI deferred; principle demonstrated |
| D-007 | Custom React i18n context | Minimal deps; hook interface stable for Wave 3 |
| D-008 | Append-only enforcement at app layer | SQLite/Postgres trigger semantics differ |
| D-009 | Fixed WebSocket event_type enumeration | Stable contract for ATELIER Wave 3 |
| D-010 | Explicit greenlet dependency | SQLAlchemy async bridge requires it |

---

## 4. SOVEREIGN-TODO items

| Ref | Description | Owner | Wave |
|-----|-------------|-------|------|
| D-006 | Wire real HMAC-SHA256 signing key for certificates | ARCHITECT + GOVERNANCE | 3 |
| reset.py L46 | Postgres reset path (DROP TABLE CASCADE) | ARCHITECT | 3 |
| schema.sql | Postgres: change TEXT uuid columns to UUID type | ARCHITECT | 3 |
| schema.sql | Postgres: change TEXT json columns to JSONB | ARCHITECT | 3 |
| schema.sql | Postgres: change TEXT timestamps to TIMESTAMPTZ | ARCHITECT | 3 |
| schema.sql | Postgres: add BEFORE DELETE/UPDATE trigger on evidence | ARCHITECT | 3 |

---

## 5. Verification commands and output

All commands were run from the repository root (`/Users/amirhosseinkazemkhani/work/mizan`).

### Package importability

```
$ uv run python -c "import mizan; print('OK: import mizan, version', mizan.__version__)"
OK: import mizan, version 0.1.0
```

### Test suite

```
$ uv run pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.12.12, pytest-9.1.1, pluggy-1.6.0
testpaths: tests
plugins: asyncio-1.4.0, anyio-4.14.2
asyncio: mode=Mode.AUTO
collected 8 items

tests/test_health.py::test_package_importable PASSED                     [ 12%]
tests/test_health.py::test_health_endpoint_returns_200 PASSED            [ 25%]
tests/test_health.py::test_health_response_schema PASSED                 [ 37%]
tests/test_health.py::test_use_cases_list_returns_five PASSED            [ 50%]
tests/test_health.py::test_model_registration_round_trip PASSED          [ 62%]
tests/test_health.py::test_evaluation_start_returns_202 PASSED           [ 75%]
tests/test_health.py::test_evidence_not_found_returns_404 PASSED         [ 87%]
tests/test_health.py::test_certificate_not_found_returns_404 PASSED      [100%]

8 passed in 0.28s
```

### Database seed

```
$ uv run python scripts/seed.py
  Inserted 5 use cases, 8 models, 2 engine_memory rows.
Seed complete.
```

### Database state

```
Tables: ['certificates', 'controls', 'engine_memory', 'evaluations',
         'evidence', 'models', 'sqlite_sequence', 'use_cases']
models=8, use_cases=5, engine_memory=2
```

### TypeScript check

```
$ cd web && npm run lint
(no output, exit 0)
```

### Register discipline linter (ARCHITECT-owned files only)

```
$ uv run python scripts/audit/register_lint.py mizan/ tests/ scripts/seed.py \
    scripts/reset.py Makefile pyproject.toml engine/db/schema.sql
Files scanned: 23
Findings: 0
Register discipline: clean.
```

Note: ATELIER's `tokens.css` and `base.css` contain em-dashes in CSS comments.
Those files are ATELIER's responsibility and are excluded from this report.
AUDITOR should direct remediation findings for those files to ATELIER.

---

## 6. Wave 0 acceptance criteria status

| Criterion | Status |
|-----------|--------|
| Monorepo scaffolded (engine, agents, api, web, suites, docs, scripts) | PASS |
| FastAPI skeleton serving a health endpoint | PASS |
| SQLite with Postgres-ready schema (7 tables) | PASS |
| React and Vite shell with bilingual scaffolding | PASS |
| Seed and reset scripts | PASS |
| `make test` passes | PASS (8/8 tests) |
| Schema documented in docs/ARCHITECTURE.md | PASS |
| `uv run python -c "import mizan"` works | PASS |

All Wave 0 acceptance criteria are met. Wave 1 workstreams may begin.
