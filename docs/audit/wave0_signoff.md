# Wave 0 Signoff, PROVISIONAL, NOT SIGNED

Wave: 0, Foundation. Auditor: AUDITOR, via the Principal Delivery Orchestrator acting in the audit role for this wave, no build agent reviewing its own work.
Status: **SIGNED**. All blocking findings closed and re-verified by execution. Two minor findings carried forward to Wave 3.

## 1. Acceptance criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Monorepo scaffolded | Met | `engine`, `agents`, `api`, `web`, `suites`, `docs`, `scripts` all present |
| 2 | FastAPI skeleton with health endpoint | Met | `tests/test_health.py::test_health_endpoint_returns_200` passed |
| 3 | Postgres-ready schema, seven tables | Met | Queried the built database: `certificates`, `controls`, `engine_memory`, `evaluations`, `evidence`, `models`, `use_cases` |
| 4 | React and Vite shell with ATELIER tokens, bilingual from first commit | Met, pending ATELIER remediation | `web/src/i18n/` carries `en` and `ar` catalogues |
| 5 | Seed and reset scripts | Met | `make seed` reported 5 use cases, 8 models, 2 engine_memory rows |
| 6 | `make dev` and `make test` | `make test` met, 8 passed in 0.34s. `make dev` not yet asserted by AUDITOR, it is a long-running process; deferred to the Wave 3 demo-path gate | |
| 7 | Schema documented in `docs/ARCHITECTURE.md` | Met | Present, table by table |

## 2. Findings

### F0-01, CRITICAL, CLOSED WITH A RECORDED RESIDUAL. The evidence table is append-only by comment, not by constraint.
**Owner: ARCHITECT.** File: `engine/db/schema.sql:12` and the `evidence` table definition.

`schema.sql:12` states "The evidence table is append-only and content-addressed. No UPDATE". Line 160 repeats "Append-only." The built database contains **zero triggers**. The claim is documentation, and documentation does not enforce anything.

This is not a theoretical objection. The product claim is that a MIZAN certificate is credible because every score links to hashed, tamper-evident evidence. If a row can be rewritten, the hash beside it is decoration. AUDITOR demonstrated all three attacks against a copy of the built database:

```
Inserted a FAILING Arabic safety probe. hash: 066a0af67fea37082886a39a

ATTACK 1, rewrite the verdict into a pass:
  passed=1  score=1.0  stored_hash=066a0af67fea37082886a39a
  the hash still describes the ORIGINAL payload, so the row now lies about itself

ATTACK 2, rewrite the payload the hash is supposed to protect:
  stored hash    : 066a0af67fea37082886a39a
  recomputed hash: d3ddb70b34f436e7984cc3cf
  match: False

ATTACK 3, delete the evidence:
  rows remaining: 0
```

Attack 1 is the one that matters for the pitch. It converts a failed Arabic safety probe, which is the demo's gasp moment, into a pass, and leaves the hash column looking untouched. A judge who asks how MIZAN knows its evidence has not been edited currently receives the answer that a comment asks nicely.

**Closed.** ARCHITECT added five triggers, a `chain_prev_hash` column forming a per-evaluation hash chain, `scripts/verify_evidence.py`, and 14 tests. AUDITOR re-ran the attacks against a copy of the rebuilt database rather than reading the tests:

```
ATTACK 1, rewrite the verdict into a pass
  [blocked] evidence is append-only: UPDATE is prohibited by charter
ATTACK 2, rewrite the payload the hash protects
  [blocked] evidence is append-only: UPDATE is prohibited by charter
ATTACK 3, delete the evidence
  [blocked] evidence is append-only: DELETE is prohibited by charter
ATTACK 4, insert a row whose hash does not match its payload
  [BREACH]  SUCCEEDED
ATTACK 5, fork the chain with a second genesis row
  [blocked] chain_prev_hash may be empty only for the first row of an evaluation
ATTACK 6, insert a row pointing at a non-existent predecessor
  [blocked] chain_prev_hash does not reference an existing payload_hash

CONTROL, a legitimate chained insert
  [ok] succeeded

Certificates, against a real issued row:
  [blocked] flip the verdict to certified
  [blocked] swap the evidence bundle hash
  [blocked] delete the certificate
```

**Residual, accepted and recorded: attack 4 is detected rather than prevented under SQLite.** SQLite has no built-in SHA-256, so no trigger can recompute `sha256(payload)` and compare it to the supplied `payload_hash`. ARCHITECT recorded this honestly in `docs/DECISIONS.md` and supplied the Postgres remedy, a generated column over `encode(sha256(payload::bytea), 'hex')`, which closes it properly on the engine a ministry would actually deploy. Under SQLite the forged row is caught by `scripts/verify_evidence.py`, which traverses the chain, recomputes every hash and exits non-zero:

```
  Payload hash  : FAIL (1 mismatch(es))
    FAIL row 785171f9: stored=aaaaaaaaaaaaaaaa... computed=485009f6eb2e944f...
  Hash chain    : BROKEN (forked chain)
Status : COMPROMISED
exit code 1
```

The distinction between prevented and detected must be stated plainly in the pitch rather than blurred. Detected with a non-zero exit is a defensible sovereign posture; claiming prevention would not be.

**One AUDITOR error to record.** An initial pass reported a breach on certificate deletion. That was a defect in the test, not the schema: a `DELETE` matching zero rows never fires a `BEFORE DELETE` trigger, and the seeded database held no certificates. Re-tested against a real issued certificate row, all three certificate attacks were blocked. A second AUDITOR error: an exit code read through a `tail` pipe reported the verifier exiting 0 on a compromised database. Unpiped, it exits 1 correctly. Both are recorded because an auditor who hides its own false positives cannot be trusted on its true ones.

Original remediation requirement, for the record: enforce immutability in the database with `BEFORE UPDATE` and `BEFORE DELETE` triggers that raise, on `evidence` and on issued `certificates`; add a hash self-consistency check so a row whose `payload_hash` does not match `sha256(payload)` cannot be inserted; provide a verifier that recomputes every hash and the bundle hash from stored payloads; supply the Postgres equivalents alongside the SQLite ones, since the schema is claimed Postgres-ready. Tests must demonstrate that each attack above now fails.

### F0-02, CRITICAL, CLOSED. Four WCAG AA failures on the adjudication states.
**Owner: ATELIER.** File: `web/src/styles/tokens.css`.

ATELIER measured each state colour against `--surface-base` alone. The product renders those labels inside a translucent chip at 12 percent alpha, and that chip sits on registry rows using `--surface-raised`. Composited correctly, four pairings fall below 4.5:1. Reproduced by `scripts/audit/verify_contrast.py`:

- `--state-rejected-text` on its chip over a raised row: 3.97:1
- `--state-rejected-text` on its chip over the page: 4.35:1
- `--state-rejected-text` on `--surface-raised` directly: 4.45:1
- `--state-pending-text` on its chip over a raised row: 4.24:1

Rejected fails in every chip context it will actually appear in. Remediation was dispatched with the constraint that the fix must lift the text tokens rather than make the chip fill opaque, because the translucency is correct for a dark console surface.

**Closed.** ATELIER lifted `--state-rejected-text` from `--colour-rejected-500` to `--colour-rejected-400` and `--state-pending-text` from `--colour-neutral-500` to `--colour-neutral-400`. Chip fills unchanged. AUDITOR re-ran the verifier rather than accepting the report:

```
[ok]  5.79:1  AA   rejected label on its chip, page
[ok]  5.29:1  AA   rejected label on its chip, raised row
[ok]  6.48:1  AA   rejected label on page
[ok]  5.92:1  AA   rejected label on raised surface
[ok]  7.06:1  AAA  pending label on its chip, page
[ok]  6.39:1  AA   pending label on its chip, raised row
[ok]  7.98:1  AAA  pending label on page
[ok]  7.29:1  AAA  pending label on raised surface

Pairings verified: 28
Contrast: all required pairings meet their WCAG threshold.
exit 0
```

**Advisory resolved as no action.** The four chip borders sit between 1.66:1 and 2.46:1 against the row. ATELIER's position, accepted: state is carried by the fill tint and the label text, the border provides a clean edge only, and lifting four borders to 3:1 would place four competing colour bands on every registry row and break table hierarchy. WCAG 1.4.11 does not bite because the border is not the sole carrier of meaning.

### F0-03, MAJOR, CLOSED. Sixty-seven em-dash violations.
**Owner: ATELIER.** `tokens.css` 53, `base.css` 9, `atelier_wave0.md` 4, `DESIGN_SYSTEM.md` 1. Charter section 7 bans em-dashes anywhere, including code comments.

**Closed.** Section headers of the form `X, dash, Y` converted to `X: Y`; inline glosses converted to commas or semicolons by context. Re-verified by AUDITOR:

```
Files scanned: 46
Findings: 0
Register discipline: clean.
exit 0
```

### F0-05, CRITICAL, CLOSED. Typefaces load from a content delivery network, so the offline demo renders in fallback fonts.
**Owner: ATELIER.** File: `web/src/styles/tokens.css`.

Disclosed by ATELIER when asked directly, which is the correct behaviour and is recorded as such. Playfair Display, Amiri, IBM Plex Sans and IBM Plex Sans Arabic are pulled from the Google Fonts content delivery network by an `@import`. With no network the page silently falls back to system faces.

This breaches the definition of done, which requires the pitch flow to run "live or offline" three consecutive times without failure, and it breaches the demo-path bias rule directly. The failure mode is the dangerous kind: invisible until it happens in the room, and total when it does, because the entire typographic register the design depends on disappears at once. Conference wifi in a competition venue is exactly the condition that triggers it.

**Closed, verified in a real browser rather than deferred.** ATELIER self-hosted 82 woff2 files with four licence texts and reported that the rendering half of the claim needed a browser it did not have. AUDITOR ran that check rather than accepting a deferral, because "the files are on disk" and "the faces render with no network" are different facts and the gap between them is where this wave's other criticals came from.

Structural: zero references to `googleapis` or `gstatic` anywhere in `web/`, all 82 `src: url()` declarations resolve to files present on disk, all 82 pass the woff2 magic-byte check, and the only remaining `@import` is a local relative one.

Rendered, via Playwright against the dev server:

```
external requests matching googleapis|gstatic : none, across the whole session
h1 computed family (English) : "Playfair Display", Georgia, "Times New Roman", serif  at 42px
language toggle              : dir=rtl, lang=ar
h1 computed family (Arabic)  : Amiri, "Traditional Arabic", "Al Bayan", serif
h1 text                      : سجل النماذج
Amiri available for Arabic   : true
loaded faces                 : Amiri 400, Amiri 700, IBM Plex Sans 400,
                               IBM Plex Sans Arabic 400, Playfair Display 700
horizontal overflow          : none, in either direction
elements outside viewport    : 0, in either direction
```

Screenshot retained at `docs/evidence/screens/mizan-wave0-rtl-clean.png`.

**An AUDITOR false alarm, recorded.** An initial pass reported Amiri unavailable, because `document.fonts.check()` uses a Latin test string by default and Amiri's faces are split by unicode-range, so the browser had correctly not yet fetched the Arabic subset for a page displaying no Arabic. Queried with Arabic text after the language switch, Amiri loads and renders. Lazy unicode-range loading is correct behaviour, not a defect, and it was not reported as one.

Original remediation, for the record: dispatched to ATELIER with a narrowly scoped exception permitting unauthenticated read-only fetches from `fonts.googleapis.com` and `fonts.gstatic.com` and nothing else. Required: local `@font-face` declarations against files in `web/public/fonts/`, a deliberate `font-display` choice with its reasoning, licence files committed per family since this is government-facing work, and verification that the faces render with the network unavailable rather than merely that the files exist on disk. Those are different facts, and the gap between them produced both criticals in this wave.

### F0-06, MINOR, OPEN. No favicon.
**Owner: ATELIER, Wave 3.** `GET /favicon.ico` returns 404 and is the only console error on the page. A broken tab icon during a live government pitch is a small thing that reads as unfinished. Cheap to fix alongside the dashboard.

### F0-07, MINOR, OPEN. Navigation items have no inline separation.
**Owner: ATELIER, Wave 3.** The three navigation links carry zero inline margin and padding inside a `display: block` parent, so in Arabic they render as one unbroken string, `السجلالتقييمالشهادات`, and would do the same in English. Not raised higher because ARCHITECT was correctly instructed to leave the shell unstyled and the component layer is Wave 3 work by charter. Recorded so it is not lost, since it is invisible in a code review and obvious on screen.

### F0-04, MINOR. `make dev` unasserted.
**Owner: AUDITOR. Partially discharged.** The Vite dev server was started and served the shell at HTTP 200 during the F0-05 verification, so the UI half is exercised. The combined `make dev` target bringing up API and UI together is still folded into the Wave 3 demo-path gate, where it is tested three consecutive times as the definition of done requires.

## 3. Gate defect found in AUDITOR's own tooling

Recorded for honesty. The first version of `register_lint.py` classified U+2713 CHECK MARK and U+2192 RIGHTWARDS ARROW as emoji and raised 20 findings against ATELIER for using them in code comments. They are dingbats and arrows, not emoji, and a tick documenting a contrast grade in a comment is legitimate technical notation. The rule was split rather than weakened: E002 now covers true emoji anywhere, and a new E004 covers dingbats and arrows only in user-facing strings, where a tick becomes a checkmark bullet and the design doctrine bans it as a generated-output tell. Both branches are regression-tested.

Three further defects were found in the same tool before it was trusted: the Python comment pattern lacked `re.MULTILINE` so only a comment on the final line of a file was scanned, the technical allowlist was global so prose could write `color` freely, and the word list omitted `analyzer`. A linter that reports clean on its first run has usually not been tested against a violation.

## 4. Commands executed

```
make test                                  8 passed in 0.34s
uv run python -c "import mizan"            0.1.0
python3 scripts/audit/register_lint.py     67 findings, all E001, all ATELIER files
python3 scripts/audit/verify_contrast.py   28 pairings, 4 failures
uv run pytest scripts/audit/test_register_lint.py   15 passed
sqlite query for triggers on the built database     NONE
```

## 5. Decision

Wave 0 is **SIGNED**. All four blocking findings, F0-01, F0-02, F0-03 and F0-05, are closed and each was re-verified by execution rather than by reading a report. F0-04 is partially discharged. F0-06 and F0-07 are minor, do not block, and are carried to Wave 3 against ATELIER.

Three AUDITOR errors are recorded in this document rather than quietly removed: a certificate-deletion false breach caused by testing a guard against an empty table, an exit code misread through a `tail` pipe, and an Amiri font false alarm caused by misunderstanding lazy unicode-range loading. An auditor that hides its own false positives cannot be trusted on its true ones.

Pattern worth recording across this wave, because it recurs. All three criticals were the same defect wearing different clothes: a property asserted in a document and never asserted against the artefact. "Append-only" written in a comment with no trigger behind it. A contrast ratio measured against a background the product never renders. A typeface named in a design system that the offline build cannot load. In each case the remedy was not closer reading but a script that recomputes the claim from the artefact itself. AUDITOR should assume, for the remainder of this engagement, that any stated property without an executable check behind it is unverified regardless of how carefully it was written.

Wave 1 is opened partially, and the reasoning is recorded rather than assumed. GOVERNANCE and RASHID have no dependency edge to either open finding: one encodes the control set and use-case repository, the other authors Arabic content and string catalogues, and neither reads evidence mutability semantics nor renders a status chip. The charter directs that work with no dependency edge is never serialised. BANDIT and HARNESS plus SENTINEL are held until F0-01 is closed, because both write and read the evidence table whose integrity guarantee is the finding.
