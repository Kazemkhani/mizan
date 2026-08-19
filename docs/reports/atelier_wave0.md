# ATELIER Wave 0 Completion Report
## Design Token System and Base Stylesheet

**Agent:** ATELIER, Design Director, Sovereign Digital Products  
**Wave:** 0  
**Files delivered:**
- `web/src/styles/tokens.css`
- `web/src/styles/base.css`
- `docs/DESIGN_SYSTEM.md`
- `web/public/fonts/` (82 woff2 files, 4 licence files)

---

## 1. Palette: Measured Contrast Ratios

Ratios taken from `verify_contrast.py` output (see §7).  The verifier
recomputes every value from the hex values in `tokens.css`; figures match
its output exactly.

### State token corrections (AUDITOR findings F0-02, F0-03)

`--state-rejected-text` lifted from `--colour-rejected-500` (`#E05560`) to
`--colour-rejected-400` (`#EA7882`).  `--state-pending-text` lifted from
`--colour-neutral-500` (`#7D8BA8`) to `--colour-neutral-400` (`#A1ADBF`).
Chip fills unchanged; translucency preserved.

| Context | Rejected `#EA7882` | Pending `#A1ADBF` | WCAG |
|---|---|---|---|
| On page | 6.48:1 | 7.98:1 | AA / AAA |
| On raised row | 5.92:1 | 7.29:1 | AA / AAA |
| Chip over page | 5.79:1 | 7.06:1 | AA / AAA |
| Chip over raised | 5.29:1 | 6.39:1 | AA / AA |

### Full contrast table

| Foreground | Background | Ratio | WCAG |
|---|---|---|---|
| `--text-primary` | `--surface-base` | 15.42:1 | AAA |
| `--text-secondary` | `--surface-base` | 10.54:1 | AAA |
| `--text-tertiary` | `--surface-base` | 7.98:1 | AAA |
| `--text-primary` | `--surface-raised` | 14.08:1 | AAA |
| `--text-secondary` | `--surface-raised` | 9.63:1 | AAA |
| `--text-primary` | `--surface-sunken` | 16.58:1 | AAA |
| `--text-accent` (gold-400) | `--surface-base` | 9.80:1 | AAA |
| `--text-accent` (gold-400) | `--surface-raised` | 8.95:1 | AAA |
| `--text-accent-strong` (gold-500) | `--surface-base` | 8.11:1 | AAA |
| `--text-accent-strong` (gold-500) | `--surface-raised` | 7.41:1 | AAA |
| `--state-certified-text` | chip over page | 5.11:1 | AA |
| `--state-certified-text` | chip over raised | 4.61:1 | AA |
| `--state-certified-text` | `--surface-base` | 5.99:1 | AA |
| `--state-certified-text` | `--surface-raised` | 5.47:1 | AA |
| `--state-in-evaluation-text` | chip over page | 7.03:1 | AAA |
| `--state-in-evaluation-text` | chip over raised | 6.37:1 | AA |
| `--state-in-evaluation-text` | `--surface-base` | 8.11:1 | AAA |
| `--state-in-evaluation-text` | `--surface-raised` | 7.41:1 | AAA |
| `--state-pending-text` | chip over page | 7.06:1 | AAA |
| `--state-pending-text` | chip over raised | 6.39:1 | AA |
| `--state-pending-text` | `--surface-base` | 7.98:1 | AAA |
| `--state-pending-text` | `--surface-raised` | 7.29:1 | AAA |
| `--state-rejected-text` | chip over page | 5.79:1 | AA |
| `--state-rejected-text` | chip over raised | 5.29:1 | AA |
| `--state-rejected-text` | `--surface-base` | 6.48:1 | AA |
| `--state-rejected-text` | `--surface-raised` | 5.92:1 | AA |
| `--text-inverse` | `--surface-inverse` | 16.70:1 | AAA |
| Gold on light (documented failure, not a token) | `--surface-inverse` | 2.06:1 | FAIL |

`--text-disabled` (2.67:1) intentionally fails AA; it signals non-interactive state.

---

## 2. Type System

### Families chosen

**Playfair Display** (Latin headings): editorial serif, high-contrast thick/thin
strokes; institutional authority matching a central bank annual report.
Weights 400, 500, 600, 700 normal; 400, 600 italic.

**Amiri** (Arabic headings): based on the Bulaq Press typeface; the established
typographic standard for Gulf federal government documentation.  Optical weight
compatible with Playfair Display.  Weights 400, 700 normal and italic.
Rejected: Cairo (Egyptian press register, not Gulf governmental); Noto Naskh
Arabic (neutral-corporate, not authoritative); Noto Kufi Arabic (kufi style
inappropriate for formal certificate register).

**IBM Plex Sans** (Latin body and UI): built for information-dense interfaces;
supports `font-variant-numeric: tabular-nums lining-nums` natively; mandatory
on all data elements.  Weights 300, 400, 500, 600 normal; 400 italic.

**IBM Plex Sans Arabic** (Arabic body and UI): same superfamily as IBM Plex Sans;
matched weights (300, 400, 500, 600 normal); eliminates optical weight clash at
script boundaries.  No italic (Arabic has no italic convention).

---

## 3. Font Self-Hosting (F0-05)

### Status: complete. `@import` removed. 82 woff2 files on disk.

The Google Fonts CDN `@import` in `tokens.css` has been replaced with 82
`@font-face` declarations referencing local files in `web/public/fonts/`.

### font-display choice: block

`font-display: block` was chosen deliberately for the live demo context.

With fonts served from localhost (the pitch machine's dev server or built
bundle), the block period is imperceptible: disk I/O for a 40 KB woff2 over
loopback is under 5 ms.  `block` ensures the correct face appears on first
paint with zero visible fallback substitution.

`swap` would schedule a fallback render then a second swap when the font
arrives.  On a projector with any timing jitter, the swap is visible and reads
as an error.  With local files, the swap happens faster than a frame, but the
risk exists and there is no benefit to accepting it.  `block` is the correct
choice when font availability is guaranteed.

### Subsetting

No additional subsetting was applied.  Google Fonts provides
unicode-range-split files (latin, latin-ext, arabic, cyrillic, vietnamese,
greek, etc.) and all subsets were downloaded.  The browser loads only the
subsets whose code points appear on the page; files for unused subsets are
never fetched.

Further subsetting was deliberately withheld.  RASHID is authoring
Arabic-native content in parallel with unknown glyph coverage.  Under-subsetting
is safe; over-subsetting produces tofu on stage.  The 82 files total 1.88 MB,
all local, so load time is not a concern in the offline demo context.

### File manifest (all 82 files verified by woff2 magic bytes)

| Family | Weights | Styles | Subsets | Files |
|---|---|---|---|---|
| Amiri | 400, 700 | normal, italic | arabic, latin-ext, latin | 12 |
| IBM Plex Sans | 300, 400, 500, 600 | normal; 400 italic | cyr-ext, cyrillic, greek, vietnamese, latin-ext, latin | 30 |
| IBM Plex Sans Arabic | 300, 400, 500, 600 | normal | arabic, cyr-ext, latin-ext, latin | 16 |
| Playfair Display | 400, 500, 600, 700 normal; 400, 600 italic | normal, italic | cyrillic, vietnamese, latin-ext, latin | 24 |
| **Total** | | | | **82 woff2, 1.88 MB** |

### Licence verification

All four families use SIL Open Font Licence 1.1.  Licence files downloaded
from canonical sources and committed to `web/public/fonts/`.

| Family | Copyright | Licence file | Source URL |
|---|---|---|---|
| Playfair Display | 2017 The Playfair Display Project Authors | `LICENSE-playfair-display.txt` | github.com/google/fonts ofl/playfairdisplay |
| Amiri | 2010-2022 The Amiri Project Authors | `LICENSE-amiri.txt` | github.com/aliftype/amiri |
| IBM Plex Sans | 2017 IBM Corp., Reserved Font Name "Plex" | `LICENSE-ibm-plex-sans.txt` | github.com/google/fonts ofl/ibmplexsans |
| IBM Plex Sans Arabic | 2017 IBM Corp., Reserved Font Name "Plex" | `LICENSE-ibm-plex-sans-arabic.txt` | github.com/google/fonts ofl/ibmplexsansarabic |

Verification method: each licence file contains the text "SIL Open Font
License, Version 1.1" and the family-specific copyright line, confirmed by
`grep -c "SIL OPEN FONT"` against each file (all returned 1).

### Offline verification: what was done and what requires a browser

**Done in this session:**

1. Cross-referenced every `src: url('/fonts/...')` declaration in `tokens.css`
   against files on disk.  82 declarations, 82 files, zero mismatches (Python
   re-parse script, output pasted in §7).
2. Verified woff2 magic bytes (`wOF2` at offset 0) for all 82 files during
   download.  Zero failures.
3. Confirmed `@import` is absent from `tokens.css` (grep returns no match).
4. Confirmed `register_lint.py` scans the updated file (now 54 files vs 46)
   and reports zero findings.

**What requires a browser to verify (must be done before the pitch):**

The claim "fonts render with no network" requires a running browser.  These
are the exact steps to verify:

1. On the pitch machine: `cd web && npm run dev` (or `vite preview` for the
   built bundle).
2. Disconnect from all networks (Wi-Fi off, Ethernet unplugged).
3. Open `http://localhost:5173` in Chrome.
4. DevTools > Network tab > filter "Font".
5. Hard-reload (Cmd+Shift+R on Mac) to bypass cache.
6. Confirm: zero requests to `fonts.googleapis.com` or `fonts.gstatic.com`.
7. Confirm: every font request returns HTTP 200 from localhost.
8. DevTools > Elements > select an `<h1>` > Computed > Font > verify
   `Playfair Display` (not Georgia or Times New Roman).
9. Select an Arabic `<h1>` > verify `Amiri`.
10. Select a data cell > verify `IBM Plex Sans`.

This is the only verification that proves the claim.  Steps 1-4 above prove
the files are present and structurally valid; only a browser proves they render.

---

## 4. Motion Vocabulary

| Token | Duration | Easing | Semantic meaning |
|---|---|---|---|
| `--duration-instant` | 80ms | standard | Toggle/checkbox; synchronous with gesture |
| `--duration-fast` | 150ms | standard | Micro-feedback: button press, row highlight |
| `--duration-normal` | 250ms | enter/exit | Panel open, tab switch |
| `--duration-deliberate` | 400ms | spring | Data movement: confidence bounds, budget bars |
| `--duration-narrative` | 600ms | decelerate | Early-stop event, certification event |
| `--duration-print` | 1200ms | standard | Certificate generation (signals cryptographic work) |

Spring easing (`cubic-bezier(0.175, 0.885, 0.32, 1.275)`) reserved for bandit
budget bars and confidence bound width changes only.  Prohibited on
layout-affecting properties (`height`, `max-height`) because overshoot causes
reflow.  All motion collapses to 0.01ms under `prefers-reduced-motion: reduce`.

---

## 5. RTL Implementation

All directional properties in both CSS files use logical properties.  Physical
forms (`left`, `right`, `padding-left`, etc.) are absent.  `dir="rtl"` on any
ancestor resolves the system correctly for Arabic without a separate stylesheet.

Number directionality inside Arabic text is handled by the Unicode Bidirectional
Algorithm.  No `unicode-bidi` overrides on numeric strings.  Arabic
`font-style: normal` enforced in `base.css` for all `:lang(ar)` / `[dir="rtl"]`
contexts (Arabic has no italic convention; Amiri must not faux-italicise).

---

## 6. Advisory: Chip Border Perceivability

Chip borders at 1.66:1 to 2.46:1 against the registry row.  Correctly
restrained.  State is carried by chip fill and label text; the border provides
a clean edge only.  Strengthening borders to 3:1 would place four competing
colour bands on every registry row and break table hierarchy.

---

## 7. Gate Execution: Real Output

### python3 scripts/audit/register_lint.py

```
Files scanned: 54
Findings: 0
Register discipline: clean.
```

Exit code: 0.  (54 files vs 46 previously; the increase is the 4 licence .txt
files, the 4 new CSS files in tokens.css, and the 82 woff2 filenames which are
not prose and are not scanned.  The lint file-type logic covers .txt as prose
and scans for em-dashes and emojis; all 4 licence files are SIL OFL boilerplate
and contain neither.)

### python3 scripts/audit/verify_contrast.py

```
Declarations parsed from the :root block: 172

[ok  ] 15.42:1  AAA   body text on page
          --text-primary #E8EDF5 on --surface-base #0A1628
[ok  ] 10.54:1  AAA   secondary text
          --text-secondary #BEC6D3 on --surface-base #0A1628
[ok  ]  7.98:1  AAA   tertiary text
          --text-tertiary #A1ADBF on --surface-base #0A1628
[ok  ] 14.08:1  AAA   body text on raised surface
          --text-primary #E8EDF5 on --surface-raised #0D1F37
[ok  ]  9.63:1  AAA   secondary on raised surface
          --text-secondary #BEC6D3 on --surface-raised #0D1F37
[ok  ] 16.58:1  AAA   body text on sunken surface
          --text-primary #E8EDF5 on --surface-sunken #040D1A
[ok  ]  9.80:1  AAA   --text-accent on page
          --text-accent #F0B52A on --surface-base #0A1628
[ok  ]  8.95:1  AAA   --text-accent on raised surface
          --text-accent #F0B52A on --surface-raised #0D1F37
[ok  ]  9.80:1  AAA   --text-accent-on-raised on page
          --text-accent-on-raised #F0B52A on --surface-base #0A1628
[ok  ]  8.95:1  AAA   --text-accent-on-raised on raised surface
          --text-accent-on-raised #F0B52A on --surface-raised #0D1F37
[ok  ]  8.11:1  AAA   --text-accent-strong on page
          --text-accent-strong #E6A000 on --surface-base #0A1628
[ok  ]  7.41:1  AAA   --text-accent-strong on raised surface
          --text-accent-strong #E6A000 on --surface-raised #0D1F37
[ok  ]  5.11:1  AA    certified label on its chip, page composited over --surface-base
          --state-certified-text #12A880 on --state-certified-surface #0B2833
[ok  ]  4.61:1  AA    certified label on its chip, raised row composited over --surface-raised
          --state-certified-text #12A880 on --state-certified-surface #0E2F40
[ok  ]  5.99:1  AA    certified label on page
          --state-certified-text #12A880 on --surface-base #0A1628
[ok  ]  5.47:1  AA    certified label on raised surface
          --state-certified-text #12A880 on --surface-raised #0D1F37
[ok  ]  7.03:1  AAA   in-evaluation label on its chip, page composited over --surface-base
          --state-in-evaluation-text #E6A000 on --state-in-evaluation-surface #202424
[ok  ]  6.37:1  AA    in-evaluation label on its chip, raised row composited over --surface-raised
          --state-in-evaluation-text #E6A000 on --state-in-evaluation-surface #232C32
[ok  ]  8.11:1  AAA   in-evaluation label on page
          --state-in-evaluation-text #E6A000 on --surface-base #0A1628
[ok  ]  7.41:1  AAA   in-evaluation label on raised surface
          --state-in-evaluation-text #E6A000 on --surface-raised #0D1F37
[ok  ]  7.06:1  AAA   pending label on its chip, page composited over --surface-base
          --state-pending-text #A1ADBF on --state-pending-surface #162235
[ok  ]  6.39:1  AA    pending label on its chip, raised row composited over --surface-raised
          --state-pending-text #A1ADBF on --state-pending-surface #182A42
[ok  ]  7.98:1  AAA   pending label on page
          --state-pending-text #A1ADBF on --surface-base #0A1628
[ok  ]  7.29:1  AAA   pending label on raised surface
          --state-pending-text #A1ADBF on --surface-raised #0D1F37
[ok  ]  5.79:1  AA    rejected label on its chip, page composited over --surface-base
          --state-rejected-text #EA7882 on --state-rejected-surface #241E2F
[ok  ]  5.29:1  AA    rejected label on its chip, raised row composited over --surface-raised
          --state-rejected-text #EA7882 on --state-rejected-surface #26253C
[ok  ]  6.48:1  AA    rejected label on page
          --state-rejected-text #EA7882 on --surface-base #0A1628
[ok  ]  5.92:1  AA    rejected label on raised surface
          --state-rejected-text #EA7882 on --surface-raised #0D1F37

Advisory, not gating. Boundary perceivability where state is already
carried by fill and label:
[note]  1.95:1        certified chip boundary against the row
[note]  2.46:1        in-evaluation chip boundary against the row
[note]  1.70:1        pending chip boundary against the row
[note]  1.66:1        rejected chip boundary against the row

Pairings verified: 28
Contrast: all required pairings meet their WCAG threshold.
```

Exit code: 0.

### Cross-reference check (src URLs vs disk)

```python
# python3 inline check
@font-face src declarations in tokens.css: 82
All referenced font files exist on disk: ok
```

---

## 8. Anti-Slop Rules Imposed on Wave 3

**Colour and surface:**  hue-shifting gradients; radial orbs or glow blobs;
dot-grid backgrounds; `backdrop-filter: blur(...)` glassmorphism; drop shadows
invisible against their background; coloured left-stripe on cards; uniform
border-radius above `--radius-md` on every surface.

**Type:** Inter, Geist, or Space Grotesk as the display or headline face;
sparkle or star icons to signal AI; emojis anywhere; em-dashes anywhere.

**Layout:** three feature cards in a row; bento grids; checkmark bullet lists
for features; fake terminal window as hero visual; hover animations applied
indiscriminately.

**Content:** English-first UI with bolted-on Arabic translation; pitch numbers
without a committed generating script; absent skeleton loaders; certificates
without a signature field.

**Register:** American spellings in authored strings, comments, tokens, and UI
copy; em-dashes; emojis.  CSS property names (`color`, `left`) stay American;
every authored word is British.

---

## 9. Outstanding: Browser Verification Required Before Pitch

The one remaining open item from F0-05 is browser-level verification of offline
font rendering.  See §3 for the exact 10-step procedure.

This cannot be done in a headless CLI environment.  It must be done on the
pitch machine before the event, by a person with Chrome open.  It takes under
three minutes.  The structural evidence (82 files, woff2 magic bytes, zero
src/disk mismatches, no @import remaining) is complete and correct.  The
rendering evidence is the gap.

---

**ATELIER Wave 0. Complete.**
