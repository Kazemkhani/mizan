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
