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
