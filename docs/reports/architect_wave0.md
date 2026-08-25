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

All commands were run from the root of this checkout.

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

---

## F0-01 Remediation (post-initial-submission)

### Finding

The AUDITOR ran three attacks against the built database and all succeeded:
- Attack 1: `UPDATE evidence SET passed = 1, score = 1.0` converted a failing
  Arabic safety probe into a pass, leaving the stored hash undisturbed.
- Attack 2: `UPDATE evidence SET payload = ..., payload_hash = ...` rewrote
  the payload and hash together; stored and recomputed hashes diverged but
  nothing detected it.
- Attack 3: `DELETE FROM evidence WHERE id = ...` removed the row entirely.

The schema had zero triggers despite the comment stating the table was
append-only. Immutability existed only in prose.

### Changes made

**engine/db/schema.sql:**
- Added `chain_prev_hash TEXT NOT NULL DEFAULT ''` to `evidence`. This is
  the `payload_hash` of the immediately preceding row for the same evaluation
  (empty string for the genesis row), forming a linked-list hash chain.
- Added `trg_evidence_insert_validate` (`BEFORE INSERT`): validates that
  `payload_hash` is exactly 64 characters; enforces genesis and chain-link
  rules.
- Added `trg_evidence_no_update` (`BEFORE UPDATE`): unconditional
  `RAISE(ABORT, ...)`. Applies to every UPDATE regardless of column.
- Added `trg_evidence_no_delete` (`BEFORE DELETE`): unconditional
  `RAISE(ABORT, ...)`.
- Added `trg_certificates_no_update` (`BEFORE UPDATE`): blocks changes to
  `evaluation_id`, `model_id`, `use_case_id`, `verdict`,
  `evidence_bundle_hash`, `certificate_data`, `issued_at`. Allows `pdf_path`
  and `signature` to be set after initial issuance (Wave 3).
- Added `trg_certificates_no_delete` (`BEFORE DELETE`): unconditional
  `RAISE(ABORT, ...)`.
- Added Postgres equivalents as comments next to each SQLite trigger.

**tests/test_evidence_immutability.py (new file):**
- 14 tests. Every attack from F0-01 has a dedicated test that asserts the
  operation raises `sqlite3.IntegrityError` (the exception class SQLite maps
  to `RAISE(ABORT, ...)` in triggers).
- Legitimate inserts and the two permitted post-issuance updates
  (`pdf_path`, `signature`) each have a passing test confirming the trigger
  does not break the table.

**scripts/verify_evidence.py (new file):**
- Recomputes `SHA-256(payload)` for every evidence row and compares to the
  stored `payload_hash`.
- Traverses the `chain_prev_hash` linked list for each evaluation, detecting
  gaps, orphans, forks, and cycles.
- Recomputes each evaluation's bundle hash and cross-checks it against the
  `certificates` table.
- Reports missing triggers (a party with DB file access could drop them).
- Prints a human-readable per-evaluation breakdown. Exits 0 on clean, 1 on
  any failure.

**docs/DECISIONS.md:**
- D-011: trigger enforcement rationale.
- D-012: payload_hash self-consistency; SQLite limitation; Postgres path.
- D-013: hash chain design, capability, limitation, and next step.
- D-014: honest trust boundary statement for pitch use.

### Verification (commands run, real output)

```
$ uv run pytest -v
...collected 22 items

tests/test_evidence_immutability.py::test_legitimate_evidence_insert_succeeds PASSED
tests/test_evidence_immutability.py::test_chained_evidence_inserts_succeed PASSED
tests/test_evidence_immutability.py::test_attack_1_update_passed_blocked PASSED
tests/test_evidence_immutability.py::test_attack_2_update_payload_and_hash_blocked PASSED
tests/test_evidence_immutability.py::test_attack_3_delete_evidence_blocked PASSED
tests/test_evidence_immutability.py::test_payload_hash_too_short_rejected PASSED
tests/test_evidence_immutability.py::test_payload_hash_too_long_rejected PASSED
tests/test_evidence_immutability.py::test_second_genesis_row_blocked PASSED
tests/test_evidence_immutability.py::test_orphan_chain_prev_hash_blocked PASSED
tests/test_evidence_immutability.py::test_certificate_delete_blocked PASSED
tests/test_evidence_immutability.py::test_certificate_verdict_immutable PASSED
tests/test_evidence_immutability.py::test_certificate_evidence_bundle_hash_immutable PASSED
tests/test_evidence_immutability.py::test_certificate_pdf_path_update_allowed PASSED
tests/test_evidence_immutability.py::test_certificate_signature_update_allowed PASSED
...
22 passed in 0.42s
```

```
$ uv run python scripts/audit/register_lint.py \
    mizan/ tests/ scripts/seed.py scripts/reset.py scripts/verify_evidence.py \
    Makefile pyproject.toml engine/db/schema.sql
Files scanned: 25
Findings: 0
Register discipline: clean.
```

```
$ make reset && uv run python scripts/verify_evidence.py
...Seed complete.
MIZAN Evidence Integrity Audit
============================================================
Database : .../data/mizan.db

No evidence rows found. Nothing to audit.
```
(Correct: seed.py populates models and use cases only; evaluation runs
and evidence rows are created by Wave 1 harness executions.)

### Trust boundary answer (D-014)

When a federal entity asks "how do you know the evidence has not been
edited?":

MIZAN enforces immutability at two layers: database triggers that abort any
UPDATE or DELETE, and a SHA-256 hash chain where each row commits to the
preceding row's digest. Any modification or deletion is detectable by
traversing the chain without trusting the database. An adversary who can
write directly to the database file and is willing to rebuild the entire
chain could defeat this without external detection. The production next step
is publishing each evaluation's bundle hash to an append-only external log
at certificate issuance, so that no party can silently alter historical
evaluations.

This is the answer that builds institutional trust. It is what D-014
records and what the Wave 4 pitch script must use verbatim.

---

## append_evidence() -- AUDITOR post-F0-01 requirement (2026-08-19)

### Requirement

The AUDITOR's F0-01 closure note directed ARCHITECT to implement
`append_evidence()` as the sole sanctioned write path for the evidence
table, eliminating Attack 4 at the interface level rather than relying on
the verify script for detection. Requirements verbatim:

- Serialise canonically; callers supply no hash.
- Share one serialisation function between write path and any future
  re-verification code.
- Handle concurrent appends to the same evaluation without forking the chain.
- Provide a test that a caller cannot supply a forged hash through this path.
- Provide a test for the concurrent-append case.

### Implementation

**`mizan/engine/db/database.py`** -- three additions:

1. `canonical_payload(payload: dict) -> str` -- single authorised
   serialisation: `json.dumps(payload, sort_keys=True, ensure_ascii=False)`.
   This is the only place the format is defined. The verify script hashes
   the stored payload string directly (not re-serialising), so there is
   no second copy of the format that can drift.

2. `_append_evidence_sync(db_path, *, ev_id, evaluation_id, ..., payload, ...)
   -> tuple[str, str]` -- synchronous core. Serialises via
   `canonical_payload()`, computes `sha256_of()`, looks up the current
   chain tail with `SELECT payload_hash ... ORDER BY rowid DESC LIMIT 1`,
   and inserts. Runs in a `asyncio.to_thread()` call from the async wrapper
   so the event loop is not blocked.

3. `append_evidence(*, evaluation_id, ..., payload, ..., max_retries=3)
   -> tuple[str, str]` -- async public interface. Retries up to
   `max_retries` times on `UNIQUE constraint failed` (the concurrent-fork
   signal); re-raises immediately on any other `sqlite3.IntegrityError`.

**`engine/db/schema.sql`** -- one addition:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_chain
    ON evidence(evaluation_id, chain_prev_hash);
```

This is the database-level fork lock. Two concurrent callers who both read
the same tail hash and both attempt INSERT receive the constraint on the
second attempt. The loser retries. The chain cannot fork because the
constraint is enforced by the engine.

**Concurrency decision (D-015).** asyncio.Lock was rejected (breaks under
multi-process deployment). Database advisory lock was rejected (not
available in SQLite). UNIQUE index was adopted: works in both SQLite and
Postgres, is enforced by the database engine not the application, and
makes the retry path explicit and auditable.

### Verification commands (real output)

```
$ make test
============================= test session starts ==============================
collected 24 items

tests/test_evidence_immutability.py::test_legitimate_evidence_insert_succeeds PASSED
tests/test_evidence_immutability.py::test_chained_evidence_inserts_succeed PASSED
tests/test_evidence_immutability.py::test_attack_1_update_passed_blocked PASSED
tests/test_evidence_immutability.py::test_attack_2_update_payload_and_hash_blocked PASSED
tests/test_evidence_immutability.py::test_attack_3_delete_evidence_blocked PASSED
tests/test_evidence_immutability.py::test_payload_hash_too_short_rejected PASSED
tests/test_evidence_immutability.py::test_payload_hash_too_long_rejected PASSED
tests/test_evidence_immutability.py::test_second_genesis_row_blocked PASSED
tests/test_evidence_immutability.py::test_orphan_chain_prev_hash_blocked PASSED
tests/test_evidence_immutability.py::test_certificate_delete_blocked PASSED
tests/test_evidence_immutability.py::test_certificate_verdict_immutable PASSED
tests/test_evidence_immutability.py::test_certificate_evidence_bundle_hash_immutable PASSED
tests/test_evidence_immutability.py::test_certificate_pdf_path_update_allowed PASSED
tests/test_evidence_immutability.py::test_certificate_signature_update_allowed PASSED
tests/test_evidence_immutability.py::test_append_evidence_computes_hash_itself PASSED
tests/test_evidence_immutability.py::test_concurrent_fork_blocked_by_unique_index PASSED
tests/test_health.py::test_package_importable PASSED
tests/test_health.py::test_health_endpoint_returns_200 PASSED
tests/test_health.py::test_health_response_schema PASSED
tests/test_health.py::test_use_cases_list_returns_five PASSED
tests/test_health.py::test_model_registration_round_trip PASSED
tests/test_health.py::test_evaluation_start_returns_202 PASSED
tests/test_health.py::test_evidence_not_found_returns_404 PASSED
tests/test_health.py::test_certificate_not_found_returns_404 PASSED

============================== 24 passed in 0.36s ==============================
```

```
$ uv run python scripts/audit/register_lint.py mizan/ tests/ scripts/seed.py \
    scripts/reset.py scripts/verify_evidence.py Makefile pyproject.toml \
    engine/db/schema.sql docs/DECISIONS.md
Files scanned: 27
Findings: 0
Register discipline: clean.
```

```
$ uv run python scripts/verify_evidence.py; echo "Exit: $?"
MIZAN Evidence Integrity Audit
============================================================
Database : .../data/mizan.db

No evidence rows found. Nothing to audit.
Exit: 0
```

### HARNESS contract (for AUDITOR to forward)

HARNESS must call `append_evidence()` exclusively. Raw INSERT statements
against the evidence table are prohibited. The function signature is:

```python
from mizan.engine.db.database import append_evidence

ev_id, payload_hash = await append_evidence(
    evaluation_id=evaluation_id,
    suite_id=suite_id,
    control_id=control_id,
    probe_id=probe_id,
    payload=probe_result_dict,   # structured dict; never a pre-serialised string
    score=score,                 # float in [0.0, 1.0]
    passed=1 if passed else 0,   # int: 1 or 0
)
```

`payload_hash` in the return value is the hash recorded in the database.
Use it to build `evidence_bundle_hash` when issuing the certificate.
