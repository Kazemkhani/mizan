# MIZAN Interface Audit
## Wave 3 Post-Build Review

**Author:** ATELIER, Design Director, Sovereign Digital Products
**Method:** Diagnosis-first. File and line for every finding. Mechanism, not vibe.
**Scope:** `web/src/` -- all screens in both languages.
**Register:** British English. No em-dashes. No emojis.
**Date:** 2026-08-20

---

## UAE Design System Compliance: Typography Amendment

**Binding standard:** The UAE Government Design System (TDRA, `designsystem.gov.ae`) applies
to all Federal Government Entities. MIZAN is federal government digital infrastructure.

**What the DLS mandates (source: `designsystem.gov.ae/guidelines/typography`, read 2026-08-20):**

- English body: Roboto
- Arabic body: Noto Kufi Arabic
- Arabic headings: Alexandria

**The Inter question (coordinator query, resolved):**

Inter appears in the `@aegov/design-system` Tailwind plugin configuration page
(`designsystem.gov.ae/docs/extending-the-configuration`), listed as the default English UI
and heading face in the plugin's preset. It is absent from the normative typography guidelines
page. These are two different authority layers.

The design doctrine bans Inter as a headline or display face on the grounds that it is the
single strongest tells in AI-generated frontend output. The doctrine permits Inter as a body
face beneath a real display face, but that case does not arise here.

**Ruling:** Inter is a plugin-default, not a guidelines mandate. The normative typography
page does not list Inter for English headings. With no mandate, the doctrine applies. Inter
is not used. Roboto (the only DLS English family in the typography guidelines) covers both
English body and English headings. Weight and scale differentiate heading from body text.

**Full type stack (Wave 3 implementation):**

| Token | Family | Source |
|---|---|---|
| `--font-heading` | Roboto | DLS English; doctrine requires omitting Inter |
| `--font-body` | Roboto | DLS normative guideline |
| `--font-heading-ar` | Alexandria | DLS normative guideline |
| `--font-body-ar` | Noto Kufi Arabic | DLS normative guideline |

The Wave 0 type stack (Playfair Display / Amiri / IBM Plex Sans) was well-argued for
institutional quality and is not disputed on aesthetic grounds. It does not comply with the
binding federal standard. Full compliance is the ruling; the Wave 0 faces are removed.

The certificate editorial exception case was made but is not strong enough to override
explicit coordinator instruction to default to compliance. Playfair Display and Amiri are
removed from the token layer and from `web/public/fonts/`. If a future ruling opens the
exception, restore from the Wave 0 font manifest in `docs/reports/atelier_wave0.md`.

### GRADE-style evidence tier presentation

The research is clear: confidence intervals as a primary display element are poorly understood
and psychologically aversive to non-specialists. The GRADE framework's approach, which uses
qualitative labels with plain descriptions and makes numeric evidence available beneath them,
is more appropriate for the non-statistician user.

The two evidence tiers must differ by named label and treatment, not primarily by exposing
a numeric bound. The bound remains visible for the judge who wants it, beneath the qualitative
label.

Implementation in this wave: the `cert.tier.*` strings are rewritten to GRADE-style labels.
The certificate table shows the decision basis label first, with the lower bound as a
supplementary column for technical readers.

---

## Executive Summary

Ahmed built a working, honest, structurally sound interface. The five-stage
journey is the right shape. The two-register certificate distinction exists and
is architecturally correct. The evidence view is genuinely useful. The
projected remediation is honestly labelled. The walkthrough works.

The problem Ahmed identified is real and has a specific mechanism: the
evaluation screen exposes internal machine vocabulary at the first layer of
visibility. A compliance officer sees "Probe stream", "Control board",
"probes conducted", and raw identifiers like `refusal_integrity_v1` before
they see a verdict. The machinery is in front, the meaning is behind it.

This audit names every defect at file:line and separates what must change
from what must stay.

---

## What Is Good and Must Stay

**Two-column evaluate layout** (`Evaluate.tsx:92-165`)
The probe stream alongside the control board is the correct information
architecture. It communicates that probes feed into controls; one list does
not replace the other.

**Control name translation** (`Evaluate.tsx:44-49`)
`controlName()` already converts `pri-en-002` to its human title. The board
already uses this. The finding is that the stream does not.

**Two-register certificate distinction** (`CertificateView.tsx:57-60`,
`app.css:.basis--primary`, `.basis--secondary`)
The `basis--primary` / `basis--secondary` chips exist and are styled
differently. The foundation is correct; the weight needs increasing (see F-06).

**Measured / projection separation** (`Remediation.tsx:95-105`,
`app.css:.measured-mark`, `.projection-mark`)
The green "Measured" and gold "Projection" banners are present throughout
the remediation stage and are exactly right. They must not be weakened.

**Replay banner text** (`en.interface.ts:41-44`, `ar.interface.ts:105-106`)
"No engine is reachable from this page, so MIZAN replays evaluations that the
real engine recorded against the real probe corpus." Every word of this is
correct and honest. The text is not the problem; the visual weight is (F-05).

**Evidence view detail layer** (`EvidenceView.tsx:33-81`)
Showing the raw probe ID, scorer name and SHA-256 hash in the evidence panel
is correct behaviour. This is the "one click away" layer. Raw identifiers
belong here.

**RTL implementation** (`app.css`, throughout)
All directional properties use CSS logical equivalents. No physical `left`,
`right`, `padding-left` or `margin-right` appears in the component stylesheet.
`dir="rtl"` on the html element resolves the system correctly. This is
correct and must not be changed.

**Walkthrough system** (`Walkthrough.tsx`, `App.tsx:80-100`)
The guided tour exists and covers every major screen. The spotlight and card
interaction is appropriately simple.

---

## Critical Findings

### F-01: Evaluate screen exposes raw probe IDs in the primary content layer

**File:** `web/src/platform/Evaluate.tsx`, lines 138-148  
**Severity:** Critical  
**Mechanism:** The probe stream renders `step.probe_id` directly as
`.stream__probe` and `step.suite_id.replace('suite-', '')` as `.stream__suite`.
These produce visible strings like `refusal_integrity_v1` and `safety` in the
primary content column. A compliance officer reading the stream sees internal
keys, not decisions.  
**What the user needs here:** Which safety standard was being checked, and
whether it passed. The control name is already translated by `controlName()` in
the same component but used only on the board column.  
**Fix:** Replace `stream__suite` and `stream__probe` with the translated
control name from `controlName(step.control_id)`. The raw probe ID belongs in
the evidence panel, which already shows it.

### F-02: Gauge labels use specialist vocabulary before a verdict is reached

**File:** `web/src/i18n/en.interface.ts`, lines 109-111  
**Severity:** Critical  
**Mechanism:** The four gauges above the stream read "Probes conducted" /
"Controls with evidence" / "Confidence required" / (verdict pill). "Probe" is
an internal evaluation-science term. "Controls with evidence" combines a
regulatory term with a qualifier that requires knowing what evidence means in
this context. These are the first things a user sees when the evaluation runs.  
**What the user needs here:** How many checks have been run; how many standards
have been assessed so far; what confidence level is required; and the verdict
when it arrives.  
**Fix:** "Probes conducted" to "Checks performed"; "Controls with evidence" to
"Standards assessed". These are not dumbed-down rewrites; they are accurate
translations into the vocabulary of the user rather than the vocabulary of the
engine.

### F-03: Favicon missing

**File:** `web/index.html`, line 6 (head block)  
**Severity:** Critical (returns 404 on every page load, browser tab is blank)  
**Mechanism:** No `<link rel="icon">` element in `<head>`. Every browser
requests `/favicon.ico` and receives a 404, which logs a console error and
leaves the browser tab unlabelled.  
**Fix:** Add an SVG favicon appropriate to a sovereign evaluation instrument:
a geometric scale, gold on navy.

---

## Major Findings

### F-04: `backdrop-filter: blur(12px)` used on both navigation bars

**Files:** `web/src/styles/app.css`, lines 188-190 (`.landing__bar`) and
573-575 (`.platform__bar`)  
**Severity:** Major  
**Mechanism:** Both sticky navigation bars use `backdrop-filter: blur(12px)`.
This is banned by the design doctrine (item 9: "Liquid glass / heavy
`backdrop-filter` frosting") and explicitly listed in the Wave 0 anti-slop law
imposed on Wave 3 agents. The blur is cosmetic decoration; institutional
infrastructure does not frost its navigation bar.  
**Fix:** Remove `backdrop-filter`. Increase background opacity to maintain
legibility: `rgba(10, 22, 40, 0.97)` for `platform__bar`,
`rgba(10, 22, 40, 0.95)` for `landing__bar`.

### F-05: Replay banner has the visual weight of a footnote

**Files:** `web/src/platform/Platform.tsx`, line 185; `web/src/styles/app.css`,
lines 582-588 (`.mode-note`)  
**Severity:** Major  
**Mechanism:** The mode-note element uses `--text-tertiary` at `--text-sm`
(13px) on `--surface-raised`. This is the lowest-visibility text treatment in
the design system. The replay declaration ("No engine is reachable...") is the
most important honesty statement on the platform and it renders like a legal
disclaimer.  
**What the governing principle requires:** The banner states what the product
is actually doing. It must be prominent enough that a user who has not read the
landing page still sees it.  
**Fix:** Upgrade to `--text-secondary`, `--text-base` (16px), gold left border,
gold-tinted background, `--weight-medium`. This is consistent with the
`projection-mark` treatment in the remediation stage, which already handles a
similar "this is not live evidence" declaration correctly.

### F-06: Certificate tier sentence is visually dominated by the verdict stamp

**Files:** `web/src/platform/CertificateView.tsx`, lines 57-60;
`web/src/styles/app.css`, lines 924-933 (`.certificate__tier`)  
**Severity:** Major  
**Mechanism:** The certificate header renders the title at `--text-2xl` (32px)
and the verdict stamp at `--text-lg` (20px) bold. The tier sentence, which
carries the most important honest qualification ("every mandatory control earned
a confidence bound" vs "one or more controls were settled without a confidence
bound"), is rendered at `--text-sm` (13px). The hierarchy misleads: CERTIFIED
dominates, the qualification reads like fine print.  
**What the governing principle requires:** A judge reading from the back of a
room must be able to see the evidence tier. The brief is explicit: "a large
title above a large CERTIFIED can overwhelm an honest sentence beneath it and
mislead by hierarchy while every word stays true."  
**Fix:** Increase tier font to `--text-base` (16px). For the budget tier
specifically (`certificate__tier--budget`): apply a distinct gold-tinted
background (`--colour-gold-50`) with gold text (`--colour-gold-800`) and a
wider gold left border. This makes the budget tier visually distinct from the
statistical tier at a glance, not merely at 13px reading distance.

### F-07: Navigation links have no visual separator in Arabic

**Files:** `web/src/styles/app.css`, lines 195-198 (`.landing__nav`)  
**Severity:** Major  
**Mechanism:** `.landing__nav` uses `gap: var(--space-6)` between links with no
separator character or border. In LTR, horizontal gap reads as separation. In
RTL, the same gap between Arabic script items can be ambiguous: the eye moves
right-to-left and the items flow the same direction, so whitespace alone does
not provide the same visual pause. The brief explicitly names this defect.  
**Fix:** Replace gap with inline-start borders on items after the first, using
logical properties so the border resolves to the correct visual side in both
directions. This produces a hairline separator that works in both scripts
without a direction-specific override.

### F-08: Hero section uses a radial glow behind the heading text

**Files:** `web/src/landing/Landing.tsx`, line 64; `web/src/styles/app.css`,
lines 201-213 (`.hero__glow`)  
**Severity:** Major  
**Mechanism:** `.hero__glow` is a radial gradient (`circle,
rgba(230, 160, 0, 0.16)...`) positioned behind the h1. This is banned by the
design doctrine (item 7: "Radial orbs and glow blobs behind hero text") and by
the design system contract: "The only gold glow permitted is `--shadow-focus`,
which is a ring." The glow does not survive the test: it draws attention to
itself rather than to the title.  
**Fix:** Remove `.hero__glow` from Landing.tsx and remove the CSS block. The
heading at Playfair Display `--text-4xl` on the navy foundation is sufficient
anchor. If a visual element is needed between the header and the title, a thin
hairline rule using `--border-hairline` is appropriate.

### F-09: Skip link uses "Continue" rather than "Skip to main content"

**File:** `web/src/App.tsx`, line 81  
**Severity:** Major (accessibility)  
**Mechanism:** `{t('common.continue')}` is used as the skip link text. The
`common.continue` key resolves to "Continue". An assistive technology user
navigating with a keyboard has no indication that this link skips navigation;
"Continue" reads as the call-to-action for the next workflow step.  
**Fix:** Add a dedicated key `skiplink` to the catalogues. English: "Skip to
main content". Arabic: to be set by RASHID (scaffold: "الانتقال إلى المحتوى
الرئيسي").

---

## Moderate Findings

### F-10: Stopping-reason strings still read as engine output

**File:** `web/src/i18n/en.interface.ts`, lines 113-116  
**Severity:** Moderate  
**Mechanism:** "Stopped: the probe corpus ran out" and "Stopped: a mandatory
control failed" appear in the outcome bar. "probe corpus" and "mandatory control
failed" are engine-facing phrases. A compliance officer needs a sentence about
what happened and what it means.  
**Fix:**
- `corpus_exhausted`: "Evaluation complete: all available tests were conducted"
- `mandatory_control_failed`: "Stopped: a required standard was not met"
- `hoeffding_bound_met`: "Evaluation complete: all required standards reached
  the declared confidence"
- `budget_exhausted`: "Evaluation complete: the test allocation was spent"

### F-11: Advisory controls not visually distinguished from mandatory controls in the certificate

**File:** `web/src/platform/CertificateView.tsx`, table rows  
**Severity:** Moderate  
**Mechanism:** The CERTIFICATE_FIELD_SPEC requires that advisory controls
(where the engine rationally declined to spend evidence) are visibly distinct
from mandatory controls that were evaluated. The current certificate table
renders all control rows alike. `common.advisory` exists in the catalogue but
is not used.  
**Note:** This requires data changes as well as UI changes (the control row must
carry an `is_mandatory` field from the certificate data). Flagged for the next
wave; the visual treatment pattern is the `basis--secondary` chip, which
already communicates "decided without statistical demonstration" and can be
extended to "advisory, not evaluated".

### F-12: Stream and board section headings are internal terms at primary visibility

**File:** `web/src/i18n/en.interface.ts`, lines 107, 109  
**Severity:** Moderate  
**Mechanism:** "Probe stream" and "Control board" are h3 headings above the
two columns. "Probe" and "board" are internal vocabulary. "Verification log"
and "Standards status" communicate the same information in the register of the
user.  
**Fix:** Rename these two string keys in the catalogue.

---

## Minor Findings

### F-13: `panel__lede` text size is 13px across all screens

**File:** `web/src/styles/app.css`, line 579 (`.panel__lede`)  
**Severity:** Minor  
**Mechanism:** `.panel__lede { font-size: var(--text-sm) }` applies 13px to
the secondary descriptive paragraph below each panel heading. The doctrine
states "Body 16px minimum." However, panel lede is support text below a
heading, not primary body text, and 13px at AAA contrast (7.98:1) passes
WCAG AA for the informational role it plays. Flagged for awareness; not a
required fix in this wave.

### F-14: `evidence.scorer` shows raw scorer ID in the evidence panel

**File:** `web/src/platform/EvidenceView.tsx`, line 56  
**Severity:** Minor  
**Mechanism:** The scorer field in the evidence panel shows the raw identifier
(`refusal_integrity_v1`). The evidence panel is the one-click-away layer where
internal detail is appropriate; however, a human-readable label alongside
the ID would complete the disclosure. "This scorer tested whether the model
refuses harmful requests" cannot be inferred from the key alone.  
**Note:** This requires a scorer-description lookup table. Flagged for the next
wave.

---

## Changes Made in This Wave

The following changes were applied to address findings F-01 through F-10 and
F-12. Each is noted below with the file changed.

| Finding | Change |
|---|---|
| F-01 | `Evaluate.tsx`: stream shows control name instead of probe ID |
| F-02 | `en.interface.ts`: "Checks performed" / "Standards assessed" |
| F-03 | `index.html`: favicon added; `public/favicon.svg`: created |
| F-04 | `app.css`: `backdrop-filter` removed from both nav bars |
| F-05 | `app.css`: mode-note upgraded to gold-tinted prominent banner |
| F-06 | `app.css`: tier font increased; budget tier gets distinct gold treatment |
| F-07 | `app.css`: nav separator added using `border-inline-start` on adjacent links |
| F-08 | `Landing.tsx` + `app.css`: hero glow removed |
| F-09 | `App.tsx` + `en.interface.ts` + `ar.interface.ts`: skip link key added |
| F-10 | `en.interface.ts`: stopping-reason strings rewritten in plain language |
| F-12 | `en.interface.ts`: "Verification log" / "Standards status" |

Arabic counterparts of changed English strings are flagged with
`# RASHID-REVIEW-REQUIRED` in `ar.interface.ts`. Arabic string values are not
changed without RASHID review.

---

## Verification Gate Results

Recorded after all changes applied. Paste real output, not claims.

```
npx tsc --noEmit            (see web/):
npm run build               (see web/):
python3 scripts/audit/register_lint.py:
python3 scripts/audit/verify_contrast.py:
```

Screenshots: `docs/evidence/screens/` after browser verification.

---

## Test for Completeness

For each screen: what would a compliance officer who has never heard of a
bandit algorithm say is happening, in their own words, within a few seconds
of looking at the screen?

**Landing:** "This is a system that tests AI models for compliance before
they go into government service. I can submit a model and get a certificate."
Pass.

**Submit:** "I drop a file here, choose from examples, and register the model."
Pass.

**Use case picker:** "I choose what the model will be used for, and the
system shows me what standards apply." Pass.

**Evaluate:** After this wave: "Tests are running. This standard passed. That
one failed. There are 11 checks performed so far." The verdict is the most
prominent element when the run completes. Pass after F-01 and F-02 fixes.

**Certificate:** "This model was certified. One or more standards were settled
without a confidence bound (clear gold callout for budget tier)." The tier
distinction is readable without reading footnotes. Pass after F-06 fix.

**Remediation:** "Here are the things the model failed. Here is the work
required to fix them. This section is labelled as a projection, not a result."
Already passes.
