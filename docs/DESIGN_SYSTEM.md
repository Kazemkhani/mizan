# MIZAN Design System Contract
## Wave 0 Token and Base Specification

**Issued by:** ATELIER, Design Director, Sovereign Digital Products  
**Target audience:** Wave 3 dashboard agents building against this contract  
**Files owned by this contract:** `web/src/styles/tokens.css`, `web/src/styles/base.css`  
**Register:** British English throughout. No em-dashes. No emojis.

---

## 1. Design Commitment

MIZAN commits to a single dark (navy) foundation. The product is simultaneously
a mission-control console and a central-bank annual report. Light or bright
themes are not provided for the main application shell. This is a deliberate
decision, not an oversight.

The exception is the `[data-theme="inverse"]` block in `tokens.css`, provided
solely for the printable certificate view rendered by the Wave 3 certificate
component. Gold text on light surfaces fails WCAG AA (measured: 2.06:1 on
`--surface-inverse`). Gold is therefore reserved exclusively for navy surfaces.

Wave 3 agents must not introduce a light mode toggle for the application shell.
If a judge opens the product in a system-light environment, the navy foundation
holds; it reads as a deliberate institutional aesthetic, which is correct.

---

## 2. Colour System

### Raw scale names

| Prefix | Range | Purpose |
|---|---|---|
| `--colour-navy-{50..950}` | 13 steps | Foundation surface layer |
| `--colour-gold-{50..900}` | 10 steps | Adjudication accent |
| `--colour-neutral-{50..950}` | 11 steps | Text, borders, chrome |
| `--colour-certified-{100..600}` | 4 steps | Certified state |
| `--colour-rejected-{100..600}` | 4 steps | Rejected state |

Components and semantic tokens must not reference raw scale values directly.
They reference semantic tokens only.

### Semantic surface tokens

| Token | Raw value | Role |
|---|---|---|
| `--surface-base` | `--colour-navy-900` | Page background |
| `--surface-raised` | `--colour-navy-850` | Cards, registry rows |
| `--surface-elevated` | `--colour-navy-800` | Side panels, drawers |
| `--surface-overlay` | `--colour-navy-750` | Dropdowns, popovers |
| `--surface-sunken` | `--colour-navy-950` | Data wells, code blocks |
| `--surface-hover` | `--colour-navy-700` | Interactive hover fill |
| `--surface-inverse` | `--colour-neutral-50` | Certificate print only |

### Contrast audit: measured ratios

All ratios use the WCAG 2.1 §1.4.3 relative luminance formula. AA minimum: 4.5:1
for body text, 3:1 for large text (18pt / 14pt bold and above). AAA: 7:1.

| Foreground | Background | Hex values | Ratio | Result |
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

**Documented failure (not a token, documented to prevent misuse):**  
Gold-500 (`#E6A000`) on surface-inverse (`#F5F6F8`): 2.06:1. Fails AA.  
Gold must never be used as text on light surfaces. Certificate text uses
`--text-inverse` (navy) on `--surface-inverse` only.

### Adjudication state colours

State colours are used as text, icons, and borders on navy surfaces. They are
NOT used as filled background chips in isolation; they appear with a
corresponding `-surface` token (low-opacity tint) and `-border` token as
a border on the tinted background. This is the only treatment that passes AA
on all navy surfaces.

| State | Token | Colour | Ratio on `--surface-base` |
|---|---|---|---|
| Certified | `--state-certified` | `#12A880` | 6.00:1 AA |
| Rejected | `--state-rejected` | `#E05560` | 4.87:1 AA |
| In Evaluation | `--state-in-evaluation` | `#E6A000` | 8.11:1 AAA |
| Pending | `--state-pending` | `#7D8BA8` | 5.29:1 AA |

---

## 3. Typography

### Family decisions

**Latin headings:** Playfair Display (weights 400, 500, 600, 700; italic 400, 600)  
High-contrast thick/thin strokes produce the institutional gravitas of an annual
report. It is NOT Inter, Geist, or Space Grotesk, all of which are prohibited
as display faces per the design anti-slop law.

**Arabic headings:** Amiri (weights 400, 700; italic 400, 700)  
Amiri is based on the Bulaq Press typeface, the typographic standard for Gulf
federal government publications and scholarly Arabic. Its optical weight at
equivalent sizes is compatible with Playfair Display. It is preferred over:
Cairo (reads as Egyptian press, not governmental); Noto Naskh Arabic (correct
but corporate-neutral rather than authoritative); Noto Kufi Arabic (kufi style
is inappropriate for this register). The CHARTER requires authentic Gulf
governmental register. Amiri satisfies this requirement; Cairo does not.

**Latin body and UI:** IBM Plex Sans (weights 300, 400, 500, 600; italic 400)  
Built explicitly for information-dense interfaces. Includes tabular lining
figures via `font-variant-numeric: tabular-nums lining-nums`, which is
mandatory for all numeric data in this product (scores, confidence bounds,
budget allocations, SHA-256 hash strings).

**Arabic body and UI:** IBM Plex Sans Arabic (weights 300, 400, 500, 600)  
Same superfamily as IBM Plex Sans. Matched weights prevent the optical weight
clash that mixing unrelated families across scripts always produces. Using a
single family for both Latin and Arabic UI text also halves the number of font
loading decisions Wave 3 agents must make.

**Two families, hard cap:** Playfair Display / Amiri (headings) and IBM Plex
Sans / IBM Plex Sans Arabic (body). A third family is not permitted unless the
Wave 3 lead obtains explicit design approval and documents the decision in
`docs/DECISIONS.md`.

### Google Fonts import

```
https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Amiri:ital,wght@0,400;0,700;1,400;1,700&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap
```

This import is already present in `tokens.css`. Do not duplicate it in
component stylesheets.

### Type scale

| Token | Value | Px equivalent | Use |
|---|---|---|---|
| `--text-xs` | 0.6875rem | 11px | Micro labels, legal footnotes |
| `--text-sm` | 0.8125rem | 13px | Secondary metadata, captions |
| `--text-base` | 1rem | 16px | Body copy (minimum) |
| `--text-md` | 1.125rem | 18px | Lead body, Arabic body |
| `--text-lg` | 1.25rem | 20px | Sub-headings, card titles |
| `--text-xl` | 1.5rem | 24px | Section headings (h3) |
| `--text-2xl` | 2rem | 32px | Page headings (h2) |
| `--text-3xl` | 2.625rem | 42px | Hero headings (h1) |
| `--text-4xl` | 3.5rem | 56px | Display titles |
| `--text-hero` | 4.5rem | 72px | Single-word landmark |

The scale deliberately skips the 20–28px range. Mid-size text on everything is
the signature of generated layout. Every element should be either clearly large
(anchor and orientation) or clearly small (data and support). This is the
design doctrine focal-point rule applied to typography.

### Arabic leading (line-height) increase

Arabic requires 15–20% more leading than Latin at equivalent sizes because of
taller ascenders, descenders below the baseline, and diacritical marks. Wave 3
agents must apply `--leading-ar-*` tokens in all `:lang(ar)` or `[dir="rtl"]`
contexts. `base.css` sets the default; component stylesheets must not override
Arabic line-height with Latin values.

### Tabular numerics — mandatory on data elements

All elements displaying evaluation scores, confidence bounds, budget
allocations, timestamps, model IDs, or SHA-256 hashes must carry:

```css
font-variant-numeric: tabular-nums lining-nums;
font-feature-settings: 'tnum' 1, 'lnum' 1;
```

`base.css` applies this to `table`, `code`, `pre`, `time`, `[data-numeric]`,
`[data-score]`, `[data-confidence]`, and `[data-budget]`. Wave 3 agents add
these attributes to the relevant data elements. Do not add tabular figures to
prose or heading text; it reads as a mechanical giveaway on non-numeric strings.

---

## 4. RTL and Bidirectional Text

### The rule

No physical directional properties (`left`, `right`, `padding-left`,
`margin-right`, `border-left`, `float: left`, etc.) appear anywhere in this
design system. Every directional property uses a CSS logical equivalent.

| Physical (banned) | Logical (use this) |
|---|---|
| `padding-left` | `padding-inline-start` |
| `padding-right` | `padding-inline-end` |
| `margin-left` | `margin-inline-start` |
| `margin-right` | `margin-inline-end` |
| `border-left` | `border-inline-start` |
| `border-right` | `border-inline-end` |
| `left: 0` (positioned) | `inset-inline-start: 0` |
| `right: 0` (positioned) | `inset-inline-end: 0` |
| `text-align: left` | `text-align: start` |
| `text-align: right` | `text-align: end` |

Setting `dir="rtl"` on the `<html>` element or on any container resolves all
logical properties correctly for Arabic. No separate RTL stylesheet is required.

### Number and punctuation directionality inside Arabic text

Western numerals (0–9) are strong left-to-right characters under the Unicode
Bidirectional Algorithm (UBA). Within an RTL paragraph, a sequence of western
numerals will render left-to-right, which is correct for this product. Scores,
model IDs, dates, and hash strings are all western numerals and should be left
to UBA without intervention.

Do NOT use `unicode-bidi: bidi-override` or `direction: ltr` on numeric
strings within Arabic paragraphs. UBA handles this correctly. Overriding UBA
will break date ranges, score sequences, and hash strings.

Arabic-Indic numerals (٠١٢٣٤٥٦٧٨٩) are classified as neutral by UBA and
resolve directionally from context. This product does not use Arabic-Indic
numerals; all numerals are western for consistency with governmental scoring
tables.

### Blockquote decorative border direction

The gold `border-inline-start` on blockquotes is defined using the logical
property. In RTL, the browser resolves this to what is visually the right edge,
which is the correct side for a decorative pull-quote rule in Arabic layout.

### Arabic and italic convention

Arabic script has no italic convention. `base.css` sets `font-style: normal` on
Arabic blockquotes to prevent browsers from synthesising a slanted glyph from
Amiri, which produces incorrect rendering. Wave 3 agents must apply
`:lang(ar) { font-style: normal }` anywhere Playfair Display italic is used
for Latin emphasis and Amiri is the active family for Arabic.

---

## 5. Spacing

The base unit is 8px. The only half-step is 4px (`--space-1`). Every component
internal padding uses `--space-2` through `--space-8`. Section padding uses
`--space-12` through `--space-32`. Page margins use `--space-20` and above.

Section padding must be varied across different sections so that sections read
at different weights. Uniform padding produces a flat, dashboard feel. The
product should feel like turning pages in an annual report: sections breathe
differently.

---

## 6. Radius

| Token | Value | Role |
|---|---|---|
| `--radius-none` | 0 | Data tables, formal rule lines |
| `--radius-sm` | 2px | Input fields, registry rows |
| `--radius-md` | 4px | Cards, panels (default) |
| `--radius-lg` | 6px | Modals, drawers |
| `--radius-full` | 9999px | Status pills, avatar thumbnails only |

Uniform `--radius-lg` or higher on every surface is a prohibited tell
(design doctrine §2, item 12). The heavy rounding that is characteristic of
consumer UI is wrong for sovereign evaluation infrastructure. Most surfaces
in this product use `--radius-md` or `--radius-sm`.

---

## 7. Elevation

Elevation on dark navy surfaces is communicated by a visible highlight edge at
the top of raised elements (inset top highlight) combined with a cast shadow.
Dark-on-dark shadows alone are invisible on `--surface-base` and are therefore
decoration, not hierarchy, which the design doctrine explicitly prohibits.

| Token | Role |
|---|---|
| `--shadow-none` | Flat; no elevation |
| `--shadow-sm` | Row hover, inactive chips |
| `--shadow-md` | Registry cards, evaluation panels |
| `--shadow-lg` | Drawers, modals |
| `--shadow-xl` | Confirmation dialogs, full-page overlays |
| `--shadow-focus` | Focus ring (not an ambient glow) |
| `--shadow-inset` | Sunken data wells |

Glassmorphism (`backdrop-filter: blur(...)`) is prohibited. It is design
doctrine item 9 and it is also a performance hazard on the evaluation theatre,
which must sustain smooth animation of confidence bounds and budget bars.

---

## 8. Motion Vocabulary

### What motion communicates in this product

| Event | Token | Duration | Easing | Visual behaviour |
|---|---|---|---|---|
| Toggle, checkbox | `--duration-instant` | 80ms | `--ease-standard` | State change feels synchronous |
| Button press, hover | `--duration-fast` | 150ms | `--ease-standard` | Micro-feedback |
| Panel open, tab switch | `--duration-normal` | 250ms | `--ease-enter` | Perceivable, not slow |
| Confidence bound update | `--duration-deliberate` | 400ms | `--ease-spring` | Data movement; readable |
| Budget reallocation | `--duration-deliberate` | 400ms | `--ease-spring` | Bandit arms shifting; the money shot |
| Early-stop event | `--duration-narrative` | 600ms | `--ease-decelerate` | Significant; demo moment |
| Certification event | `--duration-narrative` | 600ms | `--ease-decelerate` | The product's climax |
| Certificate generation | `--duration-print` | 1200ms | `--ease-standard` | Communicates cryptographic work |

### The spring easing rule

`--ease-spring` (`cubic-bezier(0.175, 0.885, 0.32, 1.275)`) is used on the
bandit budget bars and the confidence bound width changes only. The slight
overshoot communicates live data movement, not a static bar advancing. It must
not be applied to layout-affecting properties such as `height` or `max-height`
because overshoot on those causes visible reflow.

### Reduced motion

All transitions and animations are collapsed to 0.01ms under
`prefers-reduced-motion: reduce`. State changes still occur; only the temporal
expression is removed. This is in `base.css` and must not be overridden in
component stylesheets.

---

## 9. Focus Treatment

The focus ring uses gold (`--colour-gold-500`, `#E6A000`) at 2px width with a
3px offset. This is visible against all navy surfaces (measured 8.11:1 on
`--surface-base`). Mouse users do not see the ring (`:focus-visible` not
`:focus`). Keyboard and assistive technology users always see it.

Wave 3 agents must not suppress `:focus-visible` on interactive elements. The
ring is part of the design, not a browser artifact to be hidden.

---

## 10. Anti-Slop Law: What Is Banned in This Product

This section is the adversarial auditor's checklist. Every item below that
appears in a Wave 3 component is a rejection finding.

### Colour and surface
- Gradients from one vivid hue to another (`from-purple-500 to-blue-500` or
  any hue-shifting gradient). Gradients from navy-950 to navy-900 for depth
  are permitted because they stay within the dark surface language.
- Purple and black as a pairing.
- Neon accent colours; any hue with saturation above ~85% and lightness
  above ~65% on a dark background reads as neon in this product.
- Radial orbs, glow blobs, or coloured radial-gradient halos behind text.
  The only gold glow permitted is `--shadow-focus`, which is a ring.
- Dot-grid or other repeating backgrounds.
- `backdrop-filter: blur(...)` glassmorphism of any strength.
- Drop shadows whose colour is invisible against their background. See the
  elevation section for the correct dark-surface approach.
- Coloured left-stripe on cards or alert banners. The only stripe permitted
  is on a blockquote using `--border-accent-strong`.
- Uniform `border-radius` above `--radius-md` on every surface.

### Type
- Inter, Geist, or Space Grotesk as the display or headline face.
  IBM Plex Sans as the body font under Playfair Display is correct.
- Sparkle or star icons to signal AI status.
- Emojis anywhere in the product UI, commit messages, documents, or comments.
- Em-dashes anywhere. Use commas, semicolons, or full stops.

### Layout
- Three feature cards in a row as a visual landing structure.
- Bento grids as a primary layout.
- Checkmark bullet lists for feature claims.
- Fake terminal window as a hero visual.
- Animated arrows.
- Hover animations applied indiscriminately. Hover states are colour changes
  and subtle elevation changes only.

### Content
- No English-first UI with bolted-on Arabic translation. Arabic and English
  are generated from the same source strings simultaneously.
- No pitch number without a committed script in `/scripts/` that produced it.
- No skeleton loaders omitted. Every loading state must be skeletal (matching
  the shape of the content it replaces), not a spinner or blank.
- No certificate without a cryptographic signature. Mock signatures are
  acceptable for the demo as long as the signature field is populated and
  carries a documented `# SOVEREIGN-TODO` annotation.

### Register
- American spellings in any authored string (documents, code comments, UI
  copy, token names). Examples of required British forms: colour, centre,
  grey, optimise, authorised, organised, recognised, behaviour, catalogue.
  CSS property names (`color`, `border-left-radius`) are specification-
  defined and remain American; only authored prose, token names in comments,
  and UI strings are affected.
- Em-dashes. See above.
- Emojis. See above.

---

## 11. Files Owned by This Contract

| File | Owned by | Do not edit |
|---|---|---|
| `web/src/styles/tokens.css` | ATELIER (Wave 0) | Wave 3 agents |
| `web/src/styles/base.css` | ATELIER (Wave 0) | Wave 3 agents |

Wave 3 agents import `tokens.css` and `base.css` from the application entry
point and build component stylesheets on top. They do not modify the token
definitions. If a token is missing or a semantic layer is needed that does not
exist, they raise a design request in `docs/DECISIONS.md` with the specific
gap described; they do not inline raw colour values.
