# ATELIER Wave 0 Completion Report
## Design Token System and Base Stylesheet

**Agent:** ATELIER, Design Director, Sovereign Digital Products  
**Wave:** 0  
**Files delivered:**
- `web/src/styles/tokens.css`
- `web/src/styles/base.css`
- `docs/DESIGN_SYSTEM.md`

---

## 1. Palette — Measured Contrast Ratios

All ratios computed using the WCAG 2.1 §1.4.3 relative luminance formula.
Measuring tool: manual calculation from hex values; methodology documented in
`DESIGN_SYSTEM.md` §2.

| Foreground token | Background token | Hex pair | Ratio | WCAG |
|---|---|---|---|---|
| `--text-primary` | `--surface-base` | `#E8EDF5` / `#0A1628` | 15.41:1 | AAA |
| `--text-secondary` | `--surface-base` | `#BEC6D3` / `#0A1628` | 10.52:1 | AAA |
| `--text-tertiary` | `--surface-base` | `#A1ADBF` / `#0A1628` | 7.99:1 | AAA |
| `--text-accent` (gold-400) | `--surface-base` | `#F0B52A` / `#0A1628` | 9.79:1 | AAA |
| `--text-accent-strong` (gold-500) | `--surface-base` | `#E6A000` / `#0A1628` | 8.11:1 | AAA |
| `--text-accent` (gold-400) | `--surface-raised` | `#F0B52A` / `#0D1F37` | 8.95:1 | AAA |
| `--text-accent-strong` (gold-500) | `--surface-raised` | `#E6A000` / `#0D1F37` | 7.41:1 | AAA |
| `--state-certified-text` | `--surface-base` | `#12A880` / `#0A1628` | 6.00:1 | AA |
| `--state-rejected-text` | `--surface-base` | `#E05560` / `#0A1628` | 4.87:1 | AA |
| `--state-in-evaluation-text` | `--surface-base` | `#E6A000` / `#0A1628` | 8.11:1 | AAA |
| `--state-pending-text` | `--surface-base` | `#7D8BA8` / `#0A1628` | 5.29:1 | AA |
| `--text-inverse` | `--surface-inverse` | `#0A1628` / `#F5F6F8` | 16.70:1 | AAA |
| Gold-500 on light (FAIL) | `--surface-inverse` | `#E6A000` / `#F5F6F8` | 2.06:1 | FAIL |

The gold-on-light failure is documented as a safety constraint in `tokens.css`
and `DESIGN_SYSTEM.md`.  Gold is reserved for navy surfaces exclusively; the
`[data-theme="inverse"]` block remaps `--text-accent` and `--text-accent-strong`
to navy values for the certificate view.

The `--text-disabled` token (#5A6585 on #0A1628, 2.67:1) intentionally fails AA;
disabled text must signal non-interactive state and must NOT be legible as
actionable content.

---

## 2. Type System

### Families chosen

**Playfair Display** (Latin headings): editorial serif with high-contrast
thick/thin strokes; institutional authority matching a central bank annual
report.  Weights 400/500/600/700 plus italic 400/600.

**Amiri** (Arabic headings): based on the Bulaq Press typeface; the established
typographic standard for Gulf federal government documentation.  Optical weight
compatible with Playfair Display.  Weights 400/700 plus italic.  Rejected
alternatives: Cairo (reads Egyptian press register, not Gulf governmental);
Noto Naskh Arabic (correct but neutral-corporate, lacking authority); Noto Kufi
Arabic (kufi style inappropriate for this formal register).

**IBM Plex Sans** (Latin body and UI): built for information-dense interfaces;
supports `font-variant-numeric: tabular-nums lining-nums` natively; mandatory
on all data elements displaying scores, bounds, budgets, IDs, and hashes.

**IBM Plex Sans Arabic** (Arabic body and UI): same superfamily; matched weight
scale (300/400/500/600); eliminates optical weight clash at script boundaries.

**Hard cap:** two families, four faces.  A third family requires documented
design approval in `docs/DECISIONS.md`.

### Arabic leading increase

Arabic requires 15-20% more leading than Latin at equivalent sizes.  Separate
`--leading-ar-*` tokens are defined and applied in `base.css` via `:lang(ar)`
and `[dir="rtl"]` selectors.  Wave 3 component authors must not override Arabic
line-height with Latin values.

---

## 3. Motion Vocabulary

| Token | Duration | Easing | Semantic meaning |
|---|---|---|---|
| `--duration-instant` | 80ms | standard | Toggle/checkbox; synchronous with gesture |
| `--duration-fast` | 150ms | standard | Micro-feedback: button press, row highlight |
| `--duration-normal` | 250ms | enter/exit | Panel open, tab switch |
| `--duration-deliberate` | 400ms | spring | Data movement: confidence bounds, budget bars |
| `--duration-narrative` | 600ms | decelerate | Early-stop event, certification event |
| `--duration-print` | 1200ms | standard | Certificate generation (signals cryptographic work) |

The spring easing (`cubic-bezier(0.175, 0.885, 0.32, 1.275)`) is applied to
the bandit budget bars and confidence bound width changes only.  The slight
overshoot communicates live data movement; it is prohibited on layout-affecting
properties such as `height` and `max-height` because overshoot causes reflow.

All motion is reduced to 0.01ms under `prefers-reduced-motion: reduce`.

---

## 4. RTL Implementation

All directional properties in both CSS files use logical properties exclusively.
Physical properties (`left`, `right`, `padding-left`, etc.) are absent.
Setting `dir="rtl"` on `<html>` or any container resolves the entire system
correctly for Arabic without a separate stylesheet.

Number directionality inside Arabic text is handled by the Unicode Bidirectional
Algorithm (UBA).  Western numerals within RTL paragraphs render left-to-right
automatically; no `unicode-bidi` overrides are applied.

Arabic `font-style: normal` is enforced in `base.css` on blockquotes and on
heading elements under `:lang(ar)` / `[dir="rtl"]`, preventing browsers from
applying faux-italic to Amiri (Arabic has no italic convention).

---

## 5. Anti-Slop Rules Imposed on Wave 3

The following are banned in all Wave 3 components.  Each is a rejection finding
by the AUDITOR.

**Colour and surface:**  hue-shifting gradients; radial orbs or glow blobs;
dot-grid backgrounds; `backdrop-filter: blur(...)` glassmorphism; drop shadows
invisible against their background surface; coloured left-stripe on cards;
uniform border-radius above `--radius-md` on every surface.

**Type:** Inter, Geist, or Space Grotesk as the display or headline face;
sparkle or star icons to signal AI; emojis anywhere; em-dashes anywhere.

**Layout:** three feature cards in a row; bento grids; checkmark bullet lists
for features; fake terminal window as hero visual; hover animations applied
indiscriminately.

**Content:** English-first UI with bolted-on Arabic translation; pitch numbers
without a committed generating script; absent skeleton loaders; certificates
without a signature field (even if mocked with a `# SOVEREIGN-TODO`).

**Register:** American spellings in authored strings, comments, tokens, and UI
copy; em-dashes; emojis.  CSS specification property names (`color`, `left`)
stay American; every authored word is British.

---

## 6. Lint Audit Results

`design-slop-lint.sh` was run after each write.  Findings:

- `[CHECK] decorative drop shadow` — flagged the elevation shadow tokens in
  `tokens.css` (mechanical pattern match).  Justified: the shadow tokens use
  a visible inset top-highlight approach for dark-surface elevation, as required
  by design doctrine §3 (Depth: "If a shadow is invisible on the background, it
  is decoration, not hierarchy").  The approach is documented inline.  Not a
  blocking finding.
- `[CHECK] pure white background` in the original `base.css` print block —
  fixed immediately: `background-color: transparent` replaces any authored white
  background in the print context.

No `[BLOCK]` findings remain.

---

## 7. Files Requiring Action from Other Agents

`web/src/styles/base.css` imports `tokens.css` via `@import './tokens.css'`.
The application entry point (created by ARCHITECT) must import `base.css` as
the single import; `tokens.css` need not be imported separately.

Wave 3 agents must not modify `tokens.css` or `base.css`.  Missing tokens or
semantic gaps must be raised in `docs/DECISIONS.md` with the specific gap
described; raw colour values must not be inlined into components.

---

**ATELIER Wave 0 — complete.**
