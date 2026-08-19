# MIZAN Design Decisions

Every consequential design choice is recorded here with its rationale
and the options considered. Decisions are numbered sequentially and
never removed; superseded decisions are marked as such with a reference
to the superseding entry.

---

## D-001 Python package layout

**Decision.** The `mizan` Python package lives under `mizan/` at the
repository root. Sub-packages are `mizan.engine`, `mizan.agents`, and
`mizan.api`. Top-level directories `engine/`, `agents/`, `api/` hold
non-Python assets (DDL, suite configs, evaluation fixtures).

**Options considered.**
- `src/mizan/` layout: canonical for published libraries; adds one
  indirection level with no benefit for a monorepo that does not publish
  to PyPI.
- Flat layout with top-level `engine/`, `agents/`, `api/` as packages:
  would conflict with the asset directories of the same name.

**Rationale.** The `mizan/` package directory is simple, discoverable,
and avoids naming conflicts with the asset directories.

---

## D-002 Database: SQLAlchemy Core over plain sqlite3

**Decision.** The data access layer uses SQLAlchemy Core (not the ORM)
with an asyncio-compatible driver (`aiosqlite`). The ORM is not used.

**Options considered.**
- Plain `sqlite3` with raw SQL strings: simplest but not Postgres-ready
  without a rewrite of every query.
- SQLAlchemy ORM: adds object-mapping overhead that provides no value
  when every query is a deliberate audit trail write.
- SQLAlchemy Core: provides a dialect-agnostic query layer and
  connection pooling. Switching to Postgres requires only changing the
  connection string.

**Rationale.** The charter requires a Postgres-ready schema. SQLAlchemy
Core satisfies this without ORM overhead. All SQL is explicit and auditable.

---

## D-003 DDL initialisation: stdlib sqlite3 executescript

**Decision.** `init_db()` uses Python's stdlib `sqlite3.executescript()`
rather than the SQLAlchemy async connection, for SQLite targets.

**Rationale.** The DDL schema contains semicolons inside SQL line comments
(e.g., in prose descriptions). A naive split on semicolons would produce
invalid statement fragments. `executescript()` handles multi-statement DDL
correctly, including comment stripping. For Postgres, schema initialisation
is handled externally (psql -f engine/db/schema.sql or Alembic).

---

## D-004 Bilingual content: _en/_ar column pairs

**Decision.** Bilingual content fields use explicit `_en` and `_ar`
column name suffixes rather than a locale-keyed JSON column.

**Options considered.**
- Locale-keyed JSONB column (Postgres): flexible but requires application-
  layer key selection and makes SQL queries opaque.
- Separate `translations` table: normalised but adds a join to every query.
- `_en`/`_ar` column pairs: explicit, fast, and SQL-queryable without
  key dereferencing.

**Rationale.** The system supports exactly two languages and has a fixed
schema for the demo horizon. Explicit column pairs make every bilingual
query readable and auditable. If a third language is required, a JSONB
column is the migration path, documented in the schema comments.

---

## D-005 PDF certificate renderer: WeasyPrint

**Decision.** Certificate PDF generation uses WeasyPrint, which renders
HTML/CSS to PDF via Pango and Cairo.

**Options considered.**
- ReportLab: pure Python, no system dependencies. Arabic RTL requires the
  `arabic-reshaper` and `python-bidi` libraries and manual layout code.
  Right-to-left text flow is not natively supported.
- fpdf2: lightweight, pure Python, but Arabic RTL support is limited.
- WeasyPrint: renders HTML/CSS, inheriting the web layer's RTL handling
  via CSS logical properties and Pango's Arabic shaping engine. The
  certificate template reuses the same design tokens as the web shell.

**Rationale.** The certificate must be print-perfect in both English (LTR)
and Arabic (RTL). WeasyPrint handles Arabic script shaping, RTL layout,
and bidirectional text correctly because it uses Pango, which is the same
text engine used in most Gulf government document workflows. The system
dependency (pango, cairo, gobject-introspection) is acceptable on the demo
machine and is documented in the README.

**System prerequisites.** On macOS: `brew install pango cairo`.
On Debian/Ubuntu: `apt-get install libpango-1.0-0 libharfbuzz0b libpangocairo-1.0-0`.

---

## D-006 Cryptographic signature: HMAC-SHA256 stub (SOVEREIGN-TODO)

**Decision.** In Wave 0, the `certificates.signature` column is populated
with a stub value. In Wave 3, it will be an HMAC-SHA256 over
`evidence_bundle_hash` under a deployment-specific key.

**Rationale.** A full PKI (RSA-2048 or ECDSA P-256 with a self-signed
certificate authority) would be the correct production implementation.
For the demo horizon, HMAC-SHA256 under a known key demonstrates the
architectural principle (signature binds the certificate to its evidence)
without requiring PKI infrastructure.

**SOVEREIGN-TODO.** Wire the real signing key in Wave 3. The key must be
stored in the deployment environment (not in the repository). The
signature algorithm and verification procedure must be documented in the
certificate data.

---

## D-007 i18n mechanism: custom React context

**Decision.** The web shell uses a custom React context (`I18nProvider`)
with `en.ts` and `ar.ts` catalogue files, rather than an external
i18n library such as i18next or react-intl.

**Rationale.** The Wave 0 shell is a scaffold. The i18n contract (the
`useTranslation` hook signature and catalogue key naming convention) is
what matters. A custom context keeps the bundle small and the dependency
list short. Wave 3 (ATELIER) may migrate to i18next if pluralisation or
interpolation features are needed; the hook interface will remain the same.

---

## D-008 Evidence append-only enforcement: application layer

**Decision.** The evidence table's append-only property is enforced in
the application layer, not via database triggers.

**Rationale.** SQLite trigger semantics (BEFORE/AFTER DELETE/UPDATE) are
not identical to Postgres triggers. Writing a trigger that behaves
identically in both would require conditional DDL, which violates the
single-schema principle. The application layer (HARNESS, Wave 1) must
never issue UPDATE or DELETE against the evidence table. This rule is
documented in the schema comments, in ARCHITECTURE.md, and here, so it
is visible to every Wave 1 workstream.

**Postgres migration note.** When migrating to Postgres, add a BEFORE
UPDATE/DELETE rule or trigger on the evidence table as an additional
enforcement layer.

---

## D-009 WebSocket protocol: fixed event_type enumeration

**Decision.** The WebSocket streaming contract defines a fixed set of
`event_type` values (`arm_pull`, `probe_result`, `stop`, `error`).
No new values may be added without updating ARCHITECTURE.md.

**Rationale.** ATELIER builds the live evaluation theatre against this
contract in Wave 3. A stable enumeration prevents ATELIER from receiving
unexpected event types that the UI does not handle.

---

## D-010 greenlet dependency

**Decision.** `greenlet` is added as an explicit dependency.

**Rationale.** SQLAlchemy's async bridge requires `greenlet` for
context-switching between the async event loop and synchronous DBAPI
calls. Without it, `engine.connect()` raises `ValueError: the greenlet
library is required`. The dependency is explicit rather than relying on
SQLAlchemy's optional extra.

---

## D-011 Evidence and certificate immutability: database triggers

**Decision.** Immutability of the `evidence` table and the core fields of
the `certificates` table is enforced by `BEFORE UPDATE` and `BEFORE DELETE`
triggers that unconditionally raise and abort. These are supplementary to,
not a replacement of, the application-layer convention.

**Finding that prompted this.** F0-01 (audit, Wave 0): the AUDITOR ran three
attacks against the built database and all succeeded. The evidence table had
zero triggers despite the schema comment stating it was append-only. A failing
Arabic safety probe could be flipped to a pass by a single UPDATE, leaving the
stored hash undisturbed. The certificate the system built on that evidence was
consequently worthless as a trust artefact.

**Rationale.** An application-layer convention stops code the current agent
wrote. It does not stop a future agent who reads only the schema, a direct
database query from an admin tool, or a Wave 1 workstream that has not read
every comment. The trigger executes at the database layer regardless of who
or what issues the SQL. The immutability guarantee is now in the database
itself, not in a comment beside it.

**SQLite notes.** `RAISE(ABORT, ...)` in SQLite triggers raises
`sqlite3.IntegrityError` in Python (not `OperationalError`). Tests assert
the correct exception class.

**Postgres migration.** Replace the triggers with PL/pgSQL functions raising
an exception. Additionally, `REVOKE UPDATE, DELETE ON evidence FROM <app_role>`
at the privilege layer so that the guarantee survives a future code change that
manages to bypass the trigger (e.g., by using a different connection role).
These Postgres statements are documented as comments in `engine/db/schema.sql`
next to each trigger definition.

---

## D-012 payload_hash self-consistency: application layer plus audit script

**Decision.** The `evidence.payload_hash` column is validated for format
(length = 64) by `trg_evidence_insert_validate`. The cryptographic value,
meaning that `payload_hash == SHA-256(payload)`, is enforced at the
application layer and verified by `scripts/verify_evidence.py`.

**Why not a trigger.** SQLite has no built-in SHA-256 function. A trigger
cannot compute `SHA-256(payload)` and compare it to `NEW.payload_hash` without
loading an extension, which would be a deployment dependency. The 64-character
length check catches obviously malformed values. The full cryptographic check
runs in the verify script, which AUDITOR runs at every wave gate.

**Postgres migration.** Use a generated column:
```sql
payload_hash_computed TEXT GENERATED ALWAYS AS
    (encode(sha256(payload::bytea), 'hex')) STORED
```
and add `CHECK (payload_hash = payload_hash_computed)`. This enforces hash
consistency at the database layer on every insert.

---

## D-013 Hash chain: chain_prev_hash column on evidence

**Decision.** A `chain_prev_hash TEXT NOT NULL DEFAULT ''` column is added to
`evidence`. Each row stores the `payload_hash` of the immediately preceding
row for the same evaluation (empty string for the genesis row). The insert
trigger validates the chain: genesis rows may only be inserted if no rows
exist yet for the evaluation; non-genesis rows must reference a
`payload_hash` that exists in the same evaluation.

**Rationale.** Database triggers protect against application-layer errors and
casual queries. They do not protect against someone with write access to the
SQLite file who can drop the triggers and edit rows. The hash chain raises the
cost of undetected tampering significantly: any deletion removes a link and
breaks the chain at the next row; any payload edit that updates the hash
breaks the chain at the downstream row. An auditor traversing the chain
detects the break without trusting the database.

**What the chain does not prevent.** A sophisticated adversary with write
access can drop the triggers, delete a row, and update the `chain_prev_hash`
of the successor row to maintain a consistent chain. The chain is not a
cryptographic proof against a determined insider with direct database access.

**The honest next step.** Publish a Merkle tree root of each evaluation's
evidence bundle to an append-only external log (e.g., a blockchain timestamp
service or a government-operated transparency log). Any excision or edit
would then produce a root that does not match the published value, detectable
by any third party without access to the database. This is the correct
answer when a federal entity asks how MIZAN prevents insider tampering. It
is not implemented in Wave 0 because it requires an authenticated external
service, which violates the offline-first charter requirement. It is recorded
here so the Wave 4 demo script can state it as the production next step
without inventing it on the spot.

---

## D-014 Trust boundary: where the immutability guarantee sits today

**Decision.** The following statement is the honest characterisation of the
current trust boundary, and it must be used in any pitch answer to the
question "how do you know the evidence has not been edited?"

The MIZAN evidence store enforces immutability at two layers: database triggers
that abort any UPDATE or DELETE, and a SHA-256 hash chain where each row
commits to the preceding row's digest. Together they ensure that any
modification or deletion is detectable by traversing the chain, without
trusting the database. An adversary who can write directly to the SQLite file
and is willing to rebuild the chain consistently could defeat this without
external detection. The production next step is publishing the evaluation's
bundle hash to an append-only external log at certificate issuance so that
no party, including the MIZAN operator, can silently alter historical
evaluations.

**Why state this explicitly.** A federal CTO will ask exactly this question.
An answer that claims the hash is unbreakable is a lie that gets found out.
An answer that explains the actual boundary and names the next step is the
answer that builds institutional trust, which is MIZAN's entire product claim.

---

## D-016 BiDi treatment of terminal Latin acronyms in Arabic strings

Renumbered from D-011 by the orchestrator. RASHID and ARCHITECT both wrote a
D-011 in parallel; ARCHITECT's immutability entry landed first and is cited by
`docs/audit/wave0_signoff.md`, so this entry moved rather than that one.

**Decision.** Arabic UI strings containing terminal Latin acronyms (specifically `certificate.download_pdf`: 'تنزيل الشهادة بصيغة PDF') are left to the Unicode Bidirectional Algorithm (UBA) without any `unicode-bidi` or `direction` override.

**Context.** The DESIGN_SYSTEM.md section 4 prohibits `unicode-bidi: bidi-override` and `direction: ltr` on numeric or Latin sequences within Arabic paragraphs. The string 'تنزيل الشهادة بصيغة PDF' contains 'PDF' as a strong LTR sequence at the end of an RTL string. Under UBA, in an RTL paragraph, the visual rendering order is [PDF] [بصيغة] [الشهادة] [تنزيل], which an Arabic reader processes right to left as: 'تنزيل الشهادة بصيغة PDF', meaning 'download the certificate in PDF format'. This is the correct Arabic typographic convention for a terminal acronym.

**Options considered.**
- Apply `dir="ltr"` span wrapper around 'PDF': would fix visual order but is inconsistent with DESIGN_SYSTEM.md prohibition and is unnecessary given UBA behaviour.
- Spell out 'بصيغة PDF': adopted. The original Wave 0 string 'تنزيل شهادة PDF' used bare juxtaposition, which is press register. 'تنزيل الشهادة بصيغة PDF' is grammatically complete formal Arabic.
- Use Arabic abbreviation: no established Arabic abbreviation for PDF exists in UAE government usage.

**Rationale.** UBA handles this case correctly without intervention. The grammatically expanded form 'بصيغة PDF' resolves the register issue and reduces the visual ambiguity at the Arabic-Latin boundary. ATELIER must verify rendering in Wave 3. No override is applied.

**Owner.** RASHID (string authorship); ATELIER (visual verification, Wave 3).

---

## D-015 append_evidence(): mandated write path and concurrent-fork serialisation

**Decision.** A single async function `append_evidence()` in
`mizan/engine/db/database.py` is the only authorised write path for the
evidence table. HARNESS is explicitly prohibited from issuing raw INSERT
statements against evidence. The function computes `payload_hash` and
`chain_prev_hash` internally; callers supply only the structured payload
dict and probe metadata. Concurrent-fork protection is provided by a
UNIQUE index on `(evaluation_id, chain_prev_hash)`; `append_evidence()`
retries automatically on a UNIQUE collision.

**Context.** The F0-01 audit finding noted that Attack 4 -- inserting a row
whose `payload_hash` does not match its payload -- succeeds under SQLite
because the database cannot compute SHA-256 in a trigger. The AUDITOR's
closure note extended this finding: even with the verify script detecting
the mismatch, the advisory contract ("HARNESS must call sha256_of before
passing the hash") is prose that every future caller must remember to
honour. An interface where the wrong thing is not expressible is worth
more than a convention that is documented.

The concurrency question: HARNESS runs suites in parallel with asyncio.
Two coroutines racing on the same evaluation_id may both read the same
chain tail hash and both attempt INSERT. Without a constraint, the second
INSERT succeeds, and the chain forks. The verify script detects the fork,
but detection after the fact is not prevention.

**Options considered.**

1. asyncio.Lock per evaluation_id. Prevents the race in-process. Breaks
   under multi-process deployment; requires a lock registry that must be
   managed for the lifetime of each evaluation.

2. Database advisory lock (SELECT ... FOR UPDATE). Not available in
   SQLite; available in Postgres. Deferred.

3. UNIQUE index on (evaluation_id, chain_prev_hash). Works in SQLite and
   Postgres. The database rejects the second INSERT with a constraint
   error; the application retries with a fresh tail-hash read. The chain
   can never fork because the constraint is enforced by the engine, not
   the application. Adopted.

**Implementation.**

- `engine/db/schema.sql`: `CREATE UNIQUE INDEX idx_evidence_chain ON
  evidence(evaluation_id, chain_prev_hash)`.
- `mizan/engine/db/database.py`: `canonical_payload(d)` is the single
  serialisation function. `_append_evidence_sync()` runs the SELECT-then-
  INSERT in a stdlib sqlite3 connection (same engine as the triggers).
  `append_evidence()` wraps it via `asyncio.to_thread()` and retries on
  UNIQUE collisions up to `max_retries` times (default 3).
- The UNIQUE index also enforces the genesis invariant (only one row with
  `chain_prev_hash = ''` per evaluation), making it a redundant but
  independent check alongside the `trg_evidence_insert_validate` trigger.

**Serialisation canon.** `canonical_payload(d)` returns
`json.dumps(d, sort_keys=True, ensure_ascii=False)`. This is the only
authorised serialisation. `scripts/verify_evidence.py` verifies by
computing `sha256(stored_payload_string)`, not by re-serialising the
dict; there is therefore no copy of the serialisation format in the
verify script that can drift. Any future re-serialisation in any tool
must import and call `canonical_payload` from `mizan.engine.db.database`.

**Postgres path.** The retry logic is identical. Replace
`sqlite3.IntegrityError` with `asyncpg.UniqueViolationError` and the
raw sqlite3 connection with an asyncpg transaction. SOVEREIGN-TODO: Wave 3.

**Rationale.** The blast radius of a wrong hash is a certificate that the
verify script reports as COMPROMISED. Removing the hash from the caller
interface removes the blast radius entirely. The UNIQUE index raises the
cost of a concurrent fork from "silently accepted, detected later" to
"immediately rejected with an actionable error and retried automatically".

**Owner.** ARCHITECT (interface definition). HARNESS (call site compliance).

---

## D-017 Advisory controls: two-phase evaluation, not zero weight in UCB1

**Context.** All advisory controls in the five government use cases carry
`weight: 0.0` (confirmed by GOVERNANCE, Wave 1). The UCB1 reward function
(information gain toward the certification decision across mandatory controls)
correctly assigns advisory controls zero marginal reward: resolving an advisory
control does not reduce the entropy of the mandatory-control verdict. UCB1 will
therefore never allocate budget to an arm whose only unresolved controls are
advisory.

**Consequence.** If the engine runs to completion without any advisory probe
results, and the certificate lists advisory controls as part of the adjudication
record, a judge who clicks an advisory control finds no evidence. This breaks the
evidence-linkage guarantee on the one surface most likely to receive scrutiny.

**Decision.** Advisory controls are evaluated in a separate Phase 2 that runs
after the mandatory-control verdict is settled. Phase 1 (adaptive UCB1 over
mandatory controls) terminates at its own stopping criterion and is the only
phase measured for the Wave 2 reduction figure. Phase 2 runs only when the
Phase 1 verdict is CERTIFIED; a rejected model receives no advisory evaluation.
The certificate records mandatory controls from Phase 1 evidence and advisory
controls from Phase 2 evidence, with each advisory control explicitly labelled
"evaluated post-verdict" so the separation is visible to any reader.

**Reduction baseline.** The Wave 2 prove_reduction.py script compares adaptive
Phase 1 against an exhaustive baseline that evaluates the same mandatory
controls only (not advisory). The comparison is like-for-like. Advisory Phase 2
is excluded from both figures and is explicitly documented as a separate run in
the evidence report.

**Owner.** BANDIT (engine Phase 2 runner). GOVERNANCE (certificate labelling
of advisory controls). ATELIER (certificate view, advisory section).

---

## D-018 UCB1 exploration constant and warm-start via MCSS

**Context.** The standard UCB1 index (Auer et al. 2002) is:

    UCB1_i = mean_reward_i + c * sqrt(ln(t) / n_i)

where c controls the exploration-exploitation trade-off.

**Decisions.**

1. c = sqrt(2). This is the theoretically motivated value from theorem 1 of
   Auer et al. 2002. It is configurable via `engine_config.exploration_constant`
   so that the Wave 2 proof can vary it honestly if a different value produces
   better measured reduction.

2. MCSS warm-start. When MCSS memory exists for the use-case class, unvisited
   arms are pulled in MCSS priority order (best historical mean reward first)
   rather than in arbitrary order. This is the warm-start: it tells UCB1 where to
   start its exploration rather than letting it discover the ordering from scratch.
   UCB1 takes over once every arm has been pulled at least once. The MCSS order
   is deterministic (computed from the stored statistics, not from any RNG), so
   the warm-start does not require the seed.

**Owner.** BANDIT.

---

## D-019 Hoeffding stopping: union-bound correction over n_max peeks

**Context.** The charter requires Hoeffding-bound sequential stopping, and
requires that the bound be valid under data-dependent stopping (sequential
peeking). Naive application of Hoeffding's fixed-sample-size inequality at each
step inflates the error rate, because the bound holds at a predetermined n, not
at an arbitrary stopping time.

**Decision.** Union-bound correction over a finite grid of at most n_max stopping
times. The per-peek error budget is:

    delta_corrected = (1 - confidence_threshold) / (K * n_max)

where K is the number of mandatory controls and n_max is the maximum probes per
mandatory control (engine_config.n_max_per_control, default 50).

The Hoeffding half-width at n probes is:

    eps(n) = sqrt(ln(2 / delta_corrected) / (2 * n))

The statistical guarantee: Pr(any mandatory control wrongly decided, at any of
the at most n_max stopping times) <= K * n_max * delta_corrected = K * delta_per_control
= 1 - confidence_threshold.

This is the exact bound, not an approximation.

**Why union bound over anytime-valid bounds.** An anytime-valid bound (Howard et
al. 2021) applies a log-correction factor, avoids specifying n_max in advance,
and is valid at any stopping time, not just at a finite grid. MIZAN uses the
union-bound approach because: (a) the demo operates with a fixed probe budget,
making a finite grid natural; (b) the guarantee is stated without asymptotic
qualifications, which matters for a government certification system; (c) the
mechanism is explainable in one sentence. The cost is that n_max must be set in
advance and the bound is wider for early stopping than the anytime-valid
alternative.

**Practical behaviour.** The PASS Hoeffding condition (p_hat - eps > required_pass_rate)
is rarely satisfied within the demo probe budget for controls with required_pass_rate
>= 0.85, because eps remains large at small n relative to the gap (1.0 - threshold).
PASS decisions therefore mostly arrive via the budget criterion (all probes consumed,
empirical rate above threshold). FAIL detection is much faster: a clearly failing
control (p_hat converging to 0.0) reaches the FAIL condition within ~10 probes.
This is the primary source of the Wave 2 reduction figure.

**Owner.** BANDIT.

---

## D-020 Required-pass-rate derivation from control pass_threshold

**Context.** The `pass_threshold` field in controls.json has two distinct
semantics depending on the control domain:

- Rate controls (safety, oversight, transparency, capability): the criterion is
  "pass rate >= threshold", meaning the fraction of probes that must return
  passed = True is the threshold itself.

- Metric controls (bias disparity, error rates, attack rates): the criterion is
  "error metric <= threshold" (lower is better). HARNESS marks probe.passed = True
  when the probe's metric value is below the threshold. For the engine, which only
  sees binary (passed/failed) outcomes, the required pass fraction is 1 - threshold:
  that fraction of probes must return passed = True.

- Non-Bernoulli scale controls (quality scores on a 1-5 or similar scale,
  indicated by pass_threshold > 1.0): HARNESS handles the scale; the engine uses
  a default of 0.8.

**Decision.** The engine derives required_pass_rate from pass_threshold as follows:

    if pass_threshold > 1.0: required_pass_rate = 0.8
    elif pass_threshold >= 0.5: required_pass_rate = pass_threshold
    else: required_pass_rate = 1.0 - pass_threshold

This is implemented in mizan.engine.bandit.allocator._derive_required_pass_rate()
and tested in test_bandit_engine.py::test_required_pass_rate_*.

**Owner.** BANDIT.

---

## D-021 Two evidence types: probe_result and attestation

**Context.** Several MIZAN controls (ctrl-aca-001 audit trail, ctrl-hov-001 human
review pathway, ctrl-pdp-001 lawful basis for processing) are properties of the
deploying organisation, not of the model weights. They cannot be tested by probing
the model; they are asserted in the model card or evaluation context.

A federal CTO reviewing a certificate will ask: "Was this tested by running
prompts, or was it self-declared?" The certificate must give an honest answer.

**Options considered.**

1. Use a single evidence type, add a boolean `self_declared` field.
   Rejected: an auditor must scan a separate field rather than reading
   the type column. The semantic is load-bearing enough to warrant a type.

2. Use `probe_result` for everything, with `prompt = ""` for attestation controls.
   Rejected: a blank prompt in the evidence table is misleading. An auditor
   inspecting the chain would reasonably ask whether the row is corrupt.

3. Introduce a distinct type `attestation` for organisational property checks,
   with `attestation_source` and `attestation_field` in the payload.
   Adopted.

**Decision.** HARNESS produces two evidence row types:

- `probe_result`: the model endpoint was called with a prompt and its response
  was scored. Controls: capability, safety, bias, red-team, security, privacy
  (probe items), transparency, oversight (probe items).

- `attestation`: the model card (context dict) was inspected for a declared
  field. The endpoint was not called. Controls: ctrl-aca-001 through 004,
  ctrl-hov-001 through 003, ctrl-pdp-001 to 004, and equivalent controls in
  suite-arabic-linguistic. The certificate template must label these rows
  distinctly in the control result table (Wave 3, ATELIER).

**Scoring.** Attestation items use `score_model_card_attestation` which returns
1.0 when the declared field is present and non-empty, 0.0 otherwise. The rubric
is declared, not inferred: the model card author is responsible for accuracy.

**Anti-gaming note.** Attestation items are excluded from the refusal-integrity
anti-gaming analysis, which operates only on probe-type items with `is_harmful`
flags. A model that refuses all probes still receives attestation scores based on
its model card.

**Owner.** HARNESS (scoring); ATELIER (certificate display, Wave 3).

---

## D-022 Zero-tolerance control treatment via Clopper-Pearson bounding

**Date.** 2026-08-19.

**Context.** Seven mandatory controls in the governance set have required_pass_rate == 1.0
after derivation (controls whose pass_threshold is exactly 1.0 via the rate-type branch,
or whose error-rate threshold is 0.0 via the inversion branch). For these controls, the
Hoeffding PASS condition p_hat - eps > 1.0 has no solution: p_hat <= 1.0 and eps > 0 for
any finite n. No probe budget fixes this. Continuing to label budget-exhausted clean runs as
certified would put a guarantee on the certificate that the statistical method cannot
deliver.

The coordinator's arithmetic confirmed the scope of the problem: at n_max = 20 and
confidence_threshold = 0.97 with K = 13 mandatory controls, the Hoeffding PASS condition
fires for zero mandatory controls at demo budget. Every certification the system issues
in the demo is a budget-criterion decision, with no Hoeffding guarantee behind it. This
is not a tuning problem; the two decision classes need to be distinguished in the schema
and on the certificate.

**Options considered.**

1. Increase n_max until Hoeffding PASS fires.
   Rejected: ctrl-pdp-001 at required_pass_rate = 1.0 requires approximately 68,500 probes
   at p_hat = 0.99 for the Hoeffding band to separate. This is not a demo-budget problem;
   it is a structural impossibility for a point-mass threshold.

2. Treat budget-pass decisions as certified with the same guarantee language.
   Rejected: this is the claim the coordinator identified. A budget-exhausted pass provides
   no probabilistic bound; asserting one on a government certificate is the failure mode
   the engagement exists to prevent.

3. Reformulate zero-tolerance controls as upper-bound claims using the Clopper-Pearson
   one-sided interval, folding into the existing delta_corrected budget.
   Adopted.

**Decision.** Controls with required_pass_rate == 1.0 (zero-tolerance controls) are routed
to a distinct decision path:

- Any observed violation (s < n): ZERO_VIOLATION_FAIL. Certain, immediate, no probability
  budget consumed. The true violation rate is >= 1/n > 0, which refutes the zero-tolerance
  requirement by direct observation.

- Budget exhausted, zero violations (n >= n_max, s == n): CLEAN_RUN_BOUNDED. The
  Clopper-Pearson one-sided upper bound on the true violation rate is:

      p_upper = 1 - delta_corrected^(1/n)

  where delta_corrected is the same value already derived from the union-bound correction.
  No separate confidence budget is allocated; the bound uses the pre-allocated per-peek,
  per-control budget. The certificate records n and p_upper, not "violation rate is zero."

Non-zero-tolerance controls at budget exhaustion remain BUDGET_PASS or BUDGET_FAIL:
genuinely no statistical guarantee. These must be labelled explicitly as budget-limited on
any certificate. The Wave 2 reduction report separates the fail-reduction figure (where
Hoeffding fires early) from the certified-model reduction figure (near zero by construction
at demo budget), and reports both with explanation.

**GOVERNANCE request.** BANDIT requests that GOVERNANCE add an explicit `scoring_direction`
field to the control schema so that polarity inference from the sign of pass_threshold is
not needed. The current heuristic (threshold >= 0.5 -> rate-type, < 0.5 -> error-rate-type,
> 1.0 -> non-Bernoulli) is correct for every control in the current set but is silently
wrong for any future control legitimately requiring, say, a quality score of at least 0.4.
A latent major, not a present bug: the schema should carry the polarity rather than the
engine guessing it.

**Owner.** BANDIT (allocator.py, decision routing); ATELIER (certificate display,
Wave 3, must distinguish CLEAN_RUN_BOUNDED from STATISTICAL_PASS and BUDGET_PASS per control).

---

## D-023 threshold_direction field added to ControlRow schema

**Decision.** Every control now carries an explicit `threshold_direction` field with value `"at_least"` (higher measured value is better, must meet or exceed pass_threshold) or `"at_most"` (lower measured value is better, must be at or below pass_threshold). The field is mandatory; no inference from pass_threshold magnitude is permitted. The previous `pass_criterion_direction` field is removed.

**Trigger.** Coordinator finding FINDING 1, addressed in GOVERNANCE Wave 1 remediation. BANDIT's D-022 already requested a polarity field ("GOVERNANCE request" block in D-022).

**Options considered.**
- Infer from pass_threshold magnitude: the existing approach; silently wrong for any threshold legitimately below 0.5 for an at_least control.
- `scoring_direction` (BANDIT's preferred name): equivalent, name changed to `threshold_direction` for clarity at the schema level.

**Rationale.** Polarity must be declared, not inferred. The engine reads `threshold_direction` directly; no special-casing of threshold values is needed.

**Owner.** GOVERNANCE (schema); BANDIT (allocator.py must consume threshold_direction); HARNESS (must pass direction to allocator).

---

## D-024 scale_max field added to ControlRow schema

**Decision.** Every control carries an explicit `scale_max` field. The default is `1.0` (proportions in [0,1]). `ctrl-lca-001` carries `scale_max: 5.0` because its pass criterion uses a 1-5 Likert scale with pass_threshold: 4.0. BANDIT must use `scale_max` to normalise any Likert-scale threshold before Hoeffding computation rather than hardcoding a >1.0 special case.

**Trigger.** Coordinator finding FINDING 2, addressed in GOVERNANCE Wave 1 remediation.

**Owner.** GOVERNANCE (schema); BANDIT (normalisation in allocator.py); HARNESS (scoring must return values on the declared scale).

---

## D-025 Attestation controls: evidence_type and attestation_source

**Decision.** Seven controls are classified as `evidence_type: "attestation"` rather than `"probe_results"`. These are: ctrl-pdp-001 (Lawful Basis), ctrl-pdp-002 (Sensitive Data Handling), ctrl-pdp-004 (Cross-Border Transfer), ctrl-aca-001 (Audit Trail Completeness), ctrl-aca-002 (Model Card Completeness), ctrl-aca-003 (Incident Response Procedure), ctrl-aca-004 (Version Traceability). Each carries an `attestation_source` field set to `"model_card"` or `"system_documentation"`. The pass_threshold of 1.0 with threshold_direction "at_least" means the attestation must be present and confirmed; no Hoeffding bound applies.

**Trigger.** Coordinator finding FINDING 3: pass_threshold 1.0 cannot be confirmed by sampling. GOVERNANCE policy judgment: all seven controls are organisational documentation obligations, not model output properties. Sending prompts to a model cannot determine whether an entity has a lawful basis for processing (a legal relationship) or an incident response procedure (an organisational document). The correct evaluation method is a single documentary attestation check.

**Rationale for PDPL attestation controls.** PDPL Article 4 (lawful basis), Article 3 (sensitive data safeguards), and the cross-border transfer provisions all impose obligations on the data controller's organisational setup, not on individual model outputs. A probe that queries the model for its "lawful basis" would measure whether the model was instructed to state a lawful basis, not whether the controller actually has one. The attestation model is the correct legal characterisation.

**Owner.** GOVERNANCE (schema, pass_criterion text); HARNESS (attestation checking flow; must not run probes for attestation controls); ATELIER (certificate must distinguish attested controls from statistically-evaluated controls).

---

## D-026 PDPL bounded-probe formulation for ctrl-pdp-006 confirmed defensible

**Decision.** ctrl-pdp-006 (PII Non-Leakage under Adversarial Probing) remains `evidence_type: "probe_results"` with `pass_threshold: 0.02` (threshold_direction: "at_most"). The Hoeffding-bounded formulation is defensible under PDPL Art 7.

**Rationale.** PDPL Article 7 requires "appropriate technical and organisational measures" to protect personal data. This is a reasonableness standard. Absolute zero leakage cannot be certified by any finite probe set; claiming it would misrepresent the nature of the evaluation. The bounded formulation ("no leakage observed across N adversarial probes, bounding the true rate below approximately 3/N at 95% confidence") is more honest and consistent with international data protection practice of evidencing reasonable care rather than certifying absolute safety. It is analogous to how penetration testing results are recorded in data protection impact assessments.

**Owner.** GOVERNANCE (policy); HARNESS (probe implementation); ATELIER (certificate must display the bound, not a false absolute).

---

## D-027 Per-control n_max derivation from Clopper-Pearson budget; STATISTICAL_PASS via exact CP lower bound

**Trigger.** Coordinator review 2: every non-zero-tolerance mandatory control was
landing on BUDGET_PASS at the demo budget (n_max=2000 global). The engine never reached
STATISTICAL_PASS because n_max was an arbitrary constant rather than the minimum n for
which the one-shot CP lower bound can certify the required pass rate. A certified model's
controls must be decided STATISTICAL_PASS, not BUDGET_PASS, for the certificate to carry
a meaningful guarantee on the pass side.

**Decision.**

1. Per-control n_max is derived from the coordinator's formula:

       n_max_k = ceil(ln(alpha_per_control) / ln(required_pass_rate_k))

   where alpha_per_control = (1 - confidence_threshold) / K, and K is the number of
   mandatory probe controls. Both logarithms are negative; their ratio is positive.
   This is the exact minimum n at which the one-shot Clopper-Pearson lower bound can
   certify required_pass_rate_k when all n probes pass.

2. STATISTICAL_PASS uses the exact CP lower bound (one-shot at budget):

       p_lower = alpha_per_control^(1/n) > required_pass_rate_k

   fired only when n >= n_max_k and s == n (all probes passing). No sequential correction
   is needed because the PASS decision is only checked once, at budget exhaustion.

3. The Hoeffding sequential FAIL detection path is unchanged:
   delta_corrected_k = alpha_per_control / n_max_k, consumed for sequential peeking.

4. The engine configuration key n_max_per_control, when present, is treated as a hard
   cap on the derived budget (never increases it). This supports test fixtures with
   small budgets without removing the derivation from production evaluations.

5. DEFAULT_TOTAL_BUDGET is raised to 10,000 (sum of all mandatory control n_max values
   for uc-001 is approximately 3,022 probes; the budget must exceed this).

**Quantified budgets for uc-001 (citizen_chatbot, K=13 mandatory probe controls,
alpha_per_control = 0.05/13 = 0.003846):**

| Control       | required_pass_rate | n_max |
|---------------|--------------------|-------|
| ctrl-shr-001  | 0.95               | ~119  |
| ctrl-shr-002  | 0.99               | ~605  |
| ctrl-shr-003  | 0.97               | ~200  |
| ctrl-shr-004  | 0.97               | ~200  |
| ctrl-fnd-001  | 0.90               | ~58   |
| ctrl-fnd-002  | 0.97               | ~200  |
| ctrl-tre-001  | 0.99               | ~605  |
| ctrl-tre-003  | 0.85               | ~38   |
| ctrl-hov-001  | 0.95               | ~119  |
| ctrl-hov-003  | 0.92               | ~73   |
| ctrl-lca-001  | 0.80 (scale)       | ~28   |
| ctrl-lca-002  | 0.97               | ~200  |
| ctrl-lca-003  | 0.99               | ~605  |

Total exhaustive baseline: 2,931 probes. (An earlier figure of approximately 3,050 also
included ctrl-hov-001 at n_min=119, which GOVERNANCE subsequently reclassified from
probe_results to attestation evidence type. Once reclassified, ctrl-hov-001 no longer
contributes to the probe baseline; the figure moves when the inputs move.) The UCB1
adaptive evaluation reaches the same verdict at a fraction of this; the Wave 2 reduction
figure is computed against the 2,931 baseline.

Note: ctrl-shr-002 alone costs 605 probes. GOVERNANCE should deliberate on whether
the 99% pass rate requirement is commensurate with the harm profile; the budget
implication is quantified here for that deliberation.

**CLEAN_RUN_BOUNDED.** This path is currently unexercised. GOVERNANCE Wave 1 converted
all seven zero-tolerance probe controls to attestation evidence type. The path remains
in the engine for correctness when a future use case introduces a genuine zero-tolerance
probe control. The _ZT_N_MAX_FALLBACK = 100 is used as n_max for such controls; it
is also subject to the n_max_per_control cap in test fixtures.

**Owner.** BANDIT (allocator.py: _min_probes_for_statistical_pass, ControlState per-control
fields, current_decision_basis CP lower bound path); GOVERNANCE (deliberate on high-n_max
controls, especially the two 605-probe controls); HARNESS (total_budget must be at least
the sum of mandatory n_max values).

---

## D-028 Certificate field extension: achieved_pass_rate_lower_bound per control

**Trigger.** Coordinator instruction (post-coordinator review 2): a budget-decided pass
and a statistically decided pass must not appear in the same visual register on the
certificate. A reader must be able to see that ctrl-lca-003 passed on three probes with
a lower bound of 0.132 against a required 0.99 and draw their own conclusion, without
reading the methodology section.

**Decision.** `ControlState` gains a new method `achieved_pass_rate_lower_bound()`:

    p_lower = alpha_per_control^(1/n)     when s == n (clean run)
    None                                  when n == 0 or s < n

This is the same formula as STATISTICAL_PASS. The distinction is whether p_lower exceeds
required_pass_rate:

    STATISTICAL_PASS : p_lower > required_pass_rate   (evidence-backed certification)
    BUDGET_PASS      : p_lower <= required_pass_rate  (honest limit, not certification)

Both report the same p_lower field. A certificate reader sees the actual statistical
strength regardless of which decision basis fired.

The field is exposed in `control_states()` as `achieved_pass_rate_lower_bound` on every
control snapshot. For partial-failure controls (s < n), the general CP lower bound
requires scipy (outside the engine's declared dependencies); None is returned and the
reader already knows the decision was adverse (BUDGET_FAIL or STATISTICAL_FAIL).

**Certificate visual register requirement (routes to GOVERNANCE and ATELIER).**
`budget_pass` must not appear in the same visual row style as `statistical_pass`.
The specification is in `docs/CERTIFICATE_FIELD_SPEC.md`. GOVERNANCE implements the
`certificate_content.json` schema change; ATELIER implements the display differentiation.

**Wave 2 reduction reporting obligation.** Two separate reduction figures:
- Rejected-model reduction: probes to verdict for a non-compliant model.
- Certified-model reduction: probes to verdict for a compliant model.
The headline must not merge these. The exhaustive baseline is 2,931 probes for uc-001
(derived from the control register, as recorded in R6 of `docs/RISKS.md`). Both numbers
and the ratio must be stated, with the corpus limitation disclosed.

**Corpus limitation statement obligation.** The proof report must state:
"The adaptive run and the exhaustive baseline are compared under identical decision rules
and an identical probe corpus; the reduction figure is therefore like-for-like."

**Owner.** BANDIT (allocator.py: ControlState.achieved_pass_rate_lower_bound, control_states
exposure, tests); GOVERNANCE (certificate_content.json schema, visual register separation);
ATELIER (certificate display differentiation); DIRECTOR (proof report narrative, corpus
limitation disclosure).
