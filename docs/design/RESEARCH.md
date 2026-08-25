# MIZAN Design Research

**Purpose:** Evidence base for design decisions on the MIZAN sovereign AI model registry interface.  
**Audience:** The designer building the submission, evaluation, and certificate screens.  
**Register:** British English. No em-dashes. No emojis. Plain, factual prose.  
**Produced:** 2026-08-20 using agent-reach (Exa web search + Jina Reader for full-page reads).

---

## Source authority hierarchy

Before acting on anything in this document, understand the weight of each source.

| Weight | Source | Reason |
|---|---|---|
| Mandatory | UAE Government Design System (TDRA) | Binding on all Federal Government Entities. Non-compliance requires internal audit and remediation. |
| Mandatory | UAE National Digital Accessibility Policy | Published policy; references WCAG 2.1 AA as the floor for federal digital services. |
| Strong practice | GOV.UK Design System | The most rigorously user-researched government design system in the world. Evidence cited per pattern. Patterns apply where UAE DLS does not prescribe. |
| Strong practice | US Web Design System (USWDS) | Strongest on accessibility specifics, especially touch targets and form input requirements. |
| Technical authority | W3C Internationalisation Working Group | Normative guidance on bidirectional text and Arabic/RTL layout. |
| Technical authority | Material Design 3 Bidirectionality | Google's component-level RTL specification, widely implemented. |
| Domain reference | Medical/regulatory communication research | Established evidence on presenting probability and uncertainty to non-specialists. |

Where UAE DLS is silent, GOV.UK provides the strongest non-Arabic-specific patterns.  
Where sources conflict, this document says so explicitly and states which to follow.

---

## 1. UAE government digital standards

These rules apply to MIZAN because it is a federal government digital service. They outrank design preferences.

### 1.1 The design system itself

The UAE Government Design System (DLS) is an initiative of the Telecommunications and Digital Government Regulatory Authority (TDRA). It is published at `designsystem.gov.ae` and maintained by TDRA. The most recent version visible at time of reading is 3.0 (updated typography guidance) with component tests referencing WCAG 2.2.

> "All federal government entities must comply with the 'Design System'. Each FGE should conduct a comprehensive internal audit to identify areas that must be addressed."

Source: https://designsystem.gov.ae/about (read 2026-08-20)  
Source: https://dgov.tdra.gov.ae/services/design-system-for-federal-governments-websites (read 2026-08-20)

MIZAN is a federal government product. The DLS rules are not optional.

### 1.2 Typography: mandated typefaces

The DLS prescribes specific typefaces. No substitution is permitted without deviation documentation.

**Arabic (primary):** Noto Kufi Arabic. Five weights. Seven sizes. This is the primary base for all Arabic content.  
**Arabic (headings/titles):** Alexandria. Four weights. Seven sizes. Secondary base for Arabic headings.  
**English (body):** Roboto.  
**English (UI/headings):** Inter. (Specified in the plugin configuration: `@aegov/design-system` via Tailwind CSS.)

Fallback chain for Arabic: `"Noto Kufi Arabic", sans-serif`.  
Fallback chain for English: `"Roboto", -apple-system, BlinkMacSystemFont, system-ui, 'Ubuntu', 'Fira Sans', sans-serif`.

All typefaces are sourced from Google Fonts. The DLS notes this allows the server to send the smallest viable file per browser.

Source: https://designsystem.gov.ae/guidelines/typography (read 2026-08-20)  
Source: https://designsystem.gov.ae/docs/extending-the-configuration (read 2026-08-20)

### 1.3 Typography: type scale

The DLS specifies a 12-size scale for the full system, with a heading scale built on a 1.333 (major third) ratio from a base unit of 16px.

**Heading scale:**

| Level | Class | Size |
|---|---|---|
| H1 Display | `text-display` | 4.75rem / 76px |
| H1 | `text-h1` | 3.875rem / 62px |
| H2 | `text-h2` | 3rem / 48px |
| H3 | `text-h3` | 2.5rem / 40px |
| H4 | `text-h4` | 2rem / 32px |
| H5 | `text-h5` | 1.625rem / 26px |
| H6 | `text-h6` | 1.25rem / 20px |

**Content scale (7 sizes for body text):**

| Class | Size | Line height |
|---|---|---|
| `text-3xl` | 1.875rem / 30px | 2.25rem / 36px |
| `text-2xl` | 1.5rem / 24px | 2rem / 32px |
| `text-xl` | 1.25rem / 20px | 1.75rem / 28px |
| `text-lg` | 1.125rem / 18px | 1.75rem / 28px |
| `text-base` | 1rem / 16px | 1.5rem / 24px |
| `text-sm` | 0.875rem / 14px | 1.25rem / 20px |
| `text-xs` | 0.75rem / 12px | 1rem / 16px |

Minimum recommended body font: 16px. The DLS states "we recommend a minimum of 16px, unless the context necessitates less."

H1 Display must be used with caution: only in banner sliders or elements occupying at least 60% of viewport height. Use `font-extralight` (200) for this size.

Source: https://designsystem.gov.ae/guidelines/typography (read 2026-08-20)

### 1.4 Typography: responsive scaling

Headings reduce by one step at screens narrower than 1024px ("one-step decrease rule"). The DLS provides the following example for `<h1>`:

```html
<h1 class="text-h3 lg:text-h2 xl:text-h1 leading-tight">
  Visit the UAE's unified digital platform
</h1>
```

The base font must never go below 1rem as a minimum without specific justification.

### 1.5 Typography: font weights

Headings: pre-configured to `font-extrabold` (800). H1 Display uses `font-extralight` (200).  
Body content: `font-normal` (400) as default. Use `font-semibold` (600) for emphasis on larger body sizes. `font-bold` (700) is acceptable for inline emphasis.

Maximum five font weights loaded per page. Do not load a weight that is not used.

### 1.6 Typography: line height and spacing

Body font Roboto at 16px base requires a minimum line-height of 1.5 for paragraph content. This is a WCAG 1.4.12 (Text Spacing) requirement, not a stylistic choice. The DLS confirms: "This will help people experiencing low vision conditions, as well as people with cognitive concerns such as Dyslexia."

Paragraph spacing: 2x the font size (per WCAG 1.4.12).  
Word spacing: at least 0.16x the font size.  
Letter spacing: 0.12x the font size (Roboto and Noto Kufi Arabic comply by default).

Large headings (H1 to H4) may use a tighter line height, reducing as size increases, never below 1rem.

Source: https://designsystem.gov.ae/guidelines/typography (read 2026-08-20)

### 1.7 Typography: line length and alignment

Recommended line length: 60 to 100 characters. Content containers should occupy approximately 60% of the grid container width at 1240px.

Alignment rules:
- English content: left-aligned. Hero section headlines may be centre-aligned.
- Arabic content: right-aligned.
- Never justify text in either language. The DLS states justified text "slows down the reading speed for users."

Source: https://designsystem.gov.ae/guidelines/typography (read 2026-08-20)

### 1.8 Colour system

The UAE DLS core palette is approved by the UAE Cabinet Office for use across all Federal Government Entities:
- Primary: AE Gold
- Secondary: AE Black

An authority may substitute its own primary colour. When doing so, it must: (a) use the colour swatch generator to create a 50-to-950 scale, (b) not replace an existing colour but add a new one, (c) update design tokens throughout.

Gradients: create within the same tonality (e.g., primary-400 to primary-600). Cross-palette gradients are permitted only between contrasting tonalities. The example given of a forbidden pairing: UAE Green with UAE Gold.

Contrast requirement for pattern backgrounds: the pattern colour must have a contrast ratio above 4.5 against the content on it. Background patterns should be no more than 8% darker than the section background.

Source: https://designsystem.gov.ae/guidelines/colour-system (read 2026-08-20)

### 1.9 Accessibility: what the UAE mandates

The UAE DLS references:
- WCAG 2.1 AA as the mandatory floor for federal government digital services.
- WCAG 2.2 in component testing (components section notes "tested for WCAG 2.2 guidelines").
- The UAE National Digital Accessibility Policy (downloadable from u.ae).
- WAI guidelines from W3C.

Specific minimum requirements:
- Keyboard navigation: the entire website must be navigable by keyboard. The Tab key must produce a visible focus state on all interactive elements.
- Screen reader compliance: `aria` attributes are mandatory where specified per component.
- Icon minimum size: 24px, per the iconography guideline.
- Browser zoom: test at 175% with no overlapping sections.
- Captions: all video content must have captions/subtitles, delivered as WebVTT, not burned in.

Source: https://designsystem.gov.ae/guidelines/accessibility (read 2026-08-20)

### 1.10 What the UAE DLS does not cover

The DLS focuses on public-facing federal websites. It does not prescribe:
- Multi-step service journey patterns (task lists, check answers, progress through a process).
- Specific form validation and error-handling patterns.
- Certificate or decision output formats.
- How to present uncertainty or evidence quality.

For these, GOV.UK provides the strongest evidence base.

---

## 2. Multi-step service journey patterns (GOV.UK)

These patterns apply where UAE DLS is silent. They are based on published user research.

### 2.1 One question per page

GOV.UK's service manual mandates starting every form with one question per page:

> "Start by splitting the form across multiple pages with each page containing just one thing: one piece of information you're telling a user, one decision they have to make, one question they have to answer."

The reasoning: users can focus on a single decision without cognitive load from adjacent questions. Screen readers hear the question only once when it is the page's `<h1>`. The label or legend becomes the page heading.

Merge pages into a single screen only when user research specifically justifies it (for example, internal tools where users repeat tasks quickly).

Source: https://www.gov.uk/service-manual/design/form-structure (read 2026-08-20)  
Source: https://design-system.service.gov.uk/patterns/question-pages/ (read 2026-08-20)

### 2.2 Multi-task services: the task list

For services that span multiple sessions or require completing multiple groups of tasks, GOV.UK prescribes the Task List pattern.

Structure:
- Group related tasks under short, action-oriented headings.
- Each task shows a status.
- Allow users to complete tasks in any order unless a dependency makes that impossible.
- Show the task list at the start of each session (not only at the start of the service).

Statuses and their visual treatment:
- "Not yet started": grey text, no background.
- "In progress": amber/blue tag.
- "Completed": black text, no background colour. This draws attention to incomplete tasks by contrast.
- "Cannot start yet": grey text, no background, row not linked.
- "There is a problem": red background.

The reasoning for "Completed" having no background: user research showed that once several tasks were completed, users scanning for what was left found coloured "Completed" tags harder to ignore than plain text, slowing scanning.

The reasoning for using sentence case: upper case in statuses made them harder to read in research.

The reasoning for linking the whole task row (not just the task name): users attempted to click status tags as if they were buttons. Linking the full row removes that confusion.

User research finding: some services removed 12-step progress indicators with no measurable effect on completion rates or time. Test without a progress indicator first.

Source: https://design-system.service.gov.uk/components/task-list/ (read 2026-08-20)  
Source: https://design-system.service.gov.uk/patterns/complete-multiple-tasks/ (read 2026-08-20)  
Source: https://designnotes.blog.gov.uk/2023/12/15/working-as-a-community-to-iterate-the-task-list-pattern/ (read 2026-08-20)

### 2.3 Progress indicators

GOV.UK's guidance is cautious:
- Test without a progress indicator first. Many services function without one.
- Improve question order, type, or count before adding an indicator.
- If added, show which step the user is on and the total number remaining.
- Do not show all questions at once, allow navigation to previous questions from the indicator, and show the current question simultaneously. That combination creates the style of indicator research found unhelpful.

Source: https://design-system.service.gov.uk/patterns/question-pages/ (read 2026-08-20)

### 2.4 Continue button conventions

The primary action button must:
- Be labelled "Continue", not "Next".
- Align to the left (right in RTL), so users do not miss it.

Source: https://design-system.service.gov.uk/patterns/question-pages/ (read 2026-08-20)

### 2.5 Confirmation and outcome pages

When a transaction completes, a confirmation page must include:
- A Panel component (GOV.UK green, or equivalent contextually appropriate colour) with a brief outcome statement.
- A reference number, if one exists.
- Details of what happens next and when.
- Contact details for the service.
- Links to what the user is likely to need next.
- A way to save a record (for example, as a PDF).

The Panel component guidance: keep panel text brief. It is only a high-level statement of what happened. Do not put interactive elements (links, buttons) inside the panel because they will fail the 3:1 contrast minimum against the panel background.

For MIZAN, the certificate itself is the outcome record. The confirmation pattern still applies to the post-submission state before the certificate is ready.

Source: https://design-system.service.gov.uk/patterns/confirmation-pages/ (read 2026-08-20)  
Source: https://design-system.service.gov.uk/components/panel/ (read 2026-08-20)

### 2.6 Touch targets (USWDS)

The USWDS targets WCAG AAA success criterion 2.5.5 (Target Size):
- Buttons: minimum 44px wide.
- Search buttons: minimum 44 x 44px (height and width, including spacing to adjacent targets).

This applies to all interactive controls in MIZAN. In practice, ensure form submit buttons, navigation links, and evaluation step controls meet 44px in both dimensions, including surrounding whitespace counted as part of the target.

Source: https://designsystem.digital.gov/components/button/accessibility-tests/ (read 2026-08-20)  
Source: https://designsystem.digital.gov/components/search/accessibility-tests/ (read 2026-08-20)

---

## 3. Validation and error handling

### 3.1 When to validate

Do not validate when the user moves away from a field (on-blur validation). Wait until the user clicks "Continue" or "Submit". The reasoning: early validation causes problems particularly for users who type slowly.

Exception: when user research specifically shows on-blur validation solves more problems than it causes for your users.

### 3.2 How to show errors

When a submission fails validation:
1. Add "Error: " to the beginning of the page `<title>` so screen readers announce the error state immediately.
2. Show an Error Summary at the top of the page and move keyboard focus to it.
3. Show inline error messages adjacent to the fields that have errors.
4. Preserve what the user entered. Never clear fields on error.

Error messages must state what went wrong and how to fix it. The GOV.UK guidance: "be clear and concise." Avoid generic messages like "There is an error."

Turn off HTML5 validation (`novalidate` on the form element). Do not add `required` to inputs. The GOV.UK design system's error components are tested for accessibility; HTML5 browser messages are not consistent across assistive technologies.

### 3.3 Error message content

Error messages should:
- Say what the user needs to do to fix the problem.
- Not blame the user.
- Not use "please" (implies a request, not a requirement).
- Not use technical jargon.
- Be specific to the field and the specific failure mode.

Source: https://design-system.service.gov.uk/components/error-message/ (read 2026-08-20)  
Source: https://design-system.service.gov.uk/patterns/validation/ (read 2026-08-20)

### 3.4 Placeholder text

The USWDS states: "Most browsers' default rendering of placeholder text does not provide a high enough contrast ratio." Avoid placeholder text as a label substitute. Labels must always be visible. Hint text beneath the label is the correct pattern for supplementary guidance.

Source: https://designsystem.digital.gov/components/text-input/ (read 2026-08-20)

---

## 4. Right-to-left and bilingual interface practice

### 4.1 Foundational rule: use markup, not CSS or Unicode control characters

For all directional control in HTML, use the `dir` attribute on elements. Do not use CSS `direction` property or Unicode control characters (RLM, LRM, etc.) where markup is available. The W3C internationalisation guidance is explicit: "Do not use CSS styling to control directionality in HTML. Use markup."

Set `dir="rtl"` on the `<html>` element when the overall document is RTL. Do not set it on `<body>`. Use `dir="auto"` on `<textarea>` and `<pre>` elements so paragraphs align based on their initial strong character.

Source: https://www.w3.org/TR/i18n-html-tech-bidi/ (read 2026-08-20)  
Source: https://www.w3.org/International/tutorials/bidi-xhtml/ (read 2026-08-20)

### 4.2 What genuinely mirrors in RTL

Based on Material Design 3 bidirectionality guidance:

**Mirror these:**
- Page layout: reading flow starts top-right, not top-left.
- Navigation: back/forward icons flip horizontally.
- Send icon: mirrors.
- Linear progress indicators: fill from right to left (except Hebrew, which stays LTR).
- Breadcrumbs: reverse order.
- Form field labels: right-aligned in Arabic context.
- Scroll bar: moves to the left side.
- Tab stops: reverse order.
- Checkmark icon: mirrors in some RTL contexts (verify by language).
- Help/question-mark icon: mirrors in Urdu and Persian, not Arabic. Verify per language.

**Do not mirror these:**
- Media controls (play, pause, seek): always LTR regardless of page direction.
- Graphs and charts: maintain LTR directionality for Persian and Urdu. Verify for Arabic on a per-chart basis; the principle is that a chart represents time or sequence which is conventionally LTR.
- Circular progress indicators: always turn clockwise.
- Clock icons and circular refresh icons: do not mirror.
- Logos and brand marks: do not mirror.
- Telephone numbers: always LTR.
- URLs and domain names: always LTR.
- Email addresses: do not reverse username and domain. The domain is always to the right of the `@` in visual presentation. Usernames can be written RTL with cursor moving left.

Source: https://m3.material.io/m3/pages/bidirectionality-rtl (read 2026-08-20)

### 4.3 Numbers, dates, units, and currency in Arabic text

This section draws on the W3C Arabic Layout Requirements document, which is the most detailed normative source on the topic.

**Numbers:**
- All Arabic numeral systems (European digits 0-9, Eastern Arabic-Indic, Arabic-Indic) are written left to right, even in an overall RTL context. Numbers progress from least significant digit on the right to most significant on the left, as in English.
- European digits (0-9) have Unicode bidi category EN (European Number).
- Arabic-Indic digits have bidi category AN (Arabic Number); Eastern Arabic-Indic digits have category EN. This causes different contextual behaviour in bidi text.

**Percent:**
- Percent sign placed LEFT of the number (i.e., preceding the number visually): ٪١٢ not ١٢٪.
- No space between percent sign and number.
- With European digits, % may appear on either side: 12% or %12.

**Currency:**
- Currency symbol placed LEFT of the number and treated as part of the number: €١٢٫٣.

**Degree:**
- Degree sign placed RIGHT of the number: ٩٩٫٥° ف.

**Quantities:**
- Space between number and unit: ١٢ كغ (12 kg).

**Dates:**
- Date notation using solidus: 2017/06/24 or ٢٠١٧/٠٦/٢٤.

**Decimal and thousands separators:**
- Arabic decimal: ٫ (U+066B), thousands: ٬ (U+066C).
- European equivalents also used: 1,234.56 or 1.234,56.

**What this means for MIZAN:**
Any numerical confidence scores, percentage thresholds, dates on certificates, and measurement units that appear in Arabic text strings must follow these conventions, not simply mirror the English layout.

Source: https://www.w3.org/International/alreq/ (Arabic Layout Requirements, read 2026-08-20)

### 4.4 Latin-script fragments inside Arabic sentences

When Latin-script identifiers (model names, version numbers, file names) appear inside an Arabic sentence, wrap them tightly in a `<span dir="ltr">` element. Do not rely on the Unicode Bidirectional Algorithm alone for injected strings; it can produce scrambled word order at line breaks.

For inline phrases where the direction is unknown at authoring time (for example, user-provided model names), use the `<bdi>` element or `dir="auto"` on the wrapping element.

Source: https://www.w3.org/TR/i18n-html-tech-bidi/ (read 2026-08-20)

### 4.5 Arabic typefaces and their government register

The UAE DLS mandates Noto Kufi Arabic for body and Alexandria for headings. These are both Kufi-style (geometric, blocky) fonts rather than Naskh (cursive, traditional). Kufi is the conventional choice for government and institutional Arabic digital typography. Naskh is conventional for long-form prose and religious text. MIZAN's institutional character is consistent with Kufi. This is not a conflict between sources; it is context alignment.

The DLS makes no specific statement about which Arabic type style is appropriate for a registry instrument versus a website. The decision to use Kufi for government institutional text is corroborated by the DLS's own choice.

### 4.6 Bilingual layout strategy

MIZAN requires both Arabic and English on every screen. The UAE DLS does not prescribe a specific layout for bilingual screens (it describes single-language pages for each locale). The following derives from RTL practice:

- Do not display both languages in the same text block without `dir` isolation.
- Side-by-side bilingual layout (Arabic right column, English left column) is navigable but increases complexity for screen readers and requires explicit reading order management.
- Top-and-bottom layout (Arabic above, English below, or vice versa) is simpler to implement accessibly and keeps each language's alignment consistent.
- If a single reading order must be chosen, the primary language of the user's preference should lead.

For MIZAN's certificate in particular: a structured layout with clearly labelled Arabic and English sections, each with its own `dir` attribute, is safer than interleaved bilingual text.

---

## 5. Presenting a graded or probabilistic result honestly

This is MIZAN's most unusual design requirement and the one with the least direct precedent.

### 5.1 Two types of uncertainty that must not look alike

Research on communicating probability to non-experts identifies two fundamentally different types of uncertainty:

**Aleatory uncertainty** (first-order): the fundamental randomness of future outcomes. Something is statistically probable at a known rate. This is what a confidence bound expresses.

**Epistemic uncertainty** (second-order): lack of knowledge. The evidence available is insufficient to determine the answer with precision. This is what "evidence exhausted" expresses.

The key finding from the medical decision-support literature: "communicating ambiguity [epistemic uncertainty] has little effect on risk perceptions, although it increases patient worry." Communicating confidence intervals is psychologically aversive and often misunderstood.

The practical implication for MIZAN: a verdict determined by a statistical confidence bound and a verdict determined by exhausting the available evidence are epistemically different claims, and their visual representations must make this difference legible to a civil servant who is not a statistician.

Source: https://decisionaid.ohri.ca/IPDAS/IPDAS-Chapter-C.pdf (read 2026-08-20)  
Source: https://journals.sagepub.com/doi/10.1177/0272989X21996328 (read 2026-08-20)

### 5.2 Visual patterns citizens already understand

Patterns that work because users have seen them before:

**A-to-G letter grades (food hygiene, EPC):** A colour-coded letter scale from deep green (best) to red (worst or urgent). The Food Hygiene Rating Scheme uses 5-to-0 (five is top, zero is "urgent improvement necessary"). Energy Performance Certificates use A-to-G. The date of the inspection is shown alongside the rating, making explicit that it is a point-in-time snapshot.

Key EPC insight from Citizens Advice research: 76% of people who have read an EPC say it is easy to understand. The A-to-G band format is one of the best-validated rating formats in public use. It implies the rating was determined against a standard, not by exhausting evidence.

**Sub-score decomposition:** The food hygiene scheme shows three sub-components in the online rating: (1) hygiene of food handling, (2) physical condition of the premises, (3) confidence in management systems. A headline grade plus visible sub-scores is a pattern the public recognises.

**Evidence quality indicators (GRADE framework):** In clinical evidence, the GRADE framework uses qualitative labels (High, Moderate, Low, Very Low evidence quality) combined with symbols (shaded circles, stars) to communicate epistemic uncertainty about the evidence base, not the conclusion. This is distinct from a confidence interval. The label tells the reader how much to trust the finding, not how probable the finding is.

Source: https://www.gov.uk/government/publications/food-hygiene-rating-scheme/food-hygiene-rating-scheme (read 2026-08-20)  
Source: https://assets.ctfassets.net/mfz4nbgura3g/1IKSUWnC84X7QqgRjPgmnI/b60cbb11afa0bfa31ddf3b32ef31b5b0/Citizens_Advice_response_to_Home_Energy_Model_consultation__Energy_Performance_Certificates.pdf (read 2026-08-20)

### 5.3 What this means for the MIZAN certificate

The certificate shows, per control, a verdict. Two distinct situations produce a verdict:

1. The evaluation engine reached a confidence bound and decided (statistical determination).
2. The evaluation engine exhausted the available evidence and decided by default (evidentiary exhaustion).

These must look visually different. Suggested principle derived from the above:

- A verdict from a statistical confidence bound should read like a food hygiene rating: a clear categorical outcome against a known scale, with the score or bound visible.
- A verdict from evidentiary exhaustion should read like a GRADE "Low evidence" qualifier: the outcome is stated, but a distinct visual marker (not a red warning, which implies failure; more like a grey qualifier) communicates that the certainty rests on limited data rather than on a confident calculation.
- Do not use confidence intervals as the primary display element. They are poorly understood by non-statisticians and increase anxiety. Use a qualitative label anchored to a description ("Determined from statistical evidence" versus "Determined from available data, evidence limited").

The UK Government's Ethics, Transparency and Accountability Framework for Automated Decision-Making states: "End users should be provided with warning labels, or disclosure requirements to ensure they understand and consent to the decision process" and "The explanation needs to be appropriate for your audience, expert or non-expert."

Source: https://www.gov.uk/government/publications/ethics-transparency-and-accountability-framework-for-automated-decision-making (read 2026-08-20)

### 5.4 Numbers versus words for probability

The research consensus from medical decision-support: "patients have a more accurate understanding of risk if probabilistic information is presented as numbers rather than words." However, numbers must come with a clear denominator or reference class.

If MIZAN displays per-control confidence percentages, the percentage needs a denominator explanation (for example, "of models of this type, X% that pass this control subsequently satisfy the compliance requirement in audit").

Use consistent formats. Do not show percentages for some controls and frequencies ("1 in 10") for others.

Source: https://decisionaid.ohri.ca/IPDAS/IPDAS-Chapter-C.pdf (read 2026-08-20)

### 5.5 What the EU AI Act says about confidence display

The EU AI Act and accompanying academic analysis support requiring confidence estimates to accompany automated decisions:

> "A Confidence estimate of the model prediction should accompany the explanation for a specific decision."

The implication: displaying no confidence indicator and only a binary pass/fail verdict is legally and ethically weaker than showing the basis for the decision. MIZAN's certificate is stronger for showing this, not weaker.

Source: https://arxiv.org/html/2404.12762v2 (read 2026-08-20)

---

## 6. What marks an interface as machine-generated

This section collects the current, specific tells. Several external sources now catalogue them systematically.

### 6.1 The convergence mechanism

AI code generation tools are trained predominantly on: shadcn/ui components, Vercel templates, Tailwind documentation examples, and marketing pages of YC-backed companies from 2022 to 2024. Human evaluators in RLHF training rated "safe" higher than "interesting," so models learned to produce statistically average output. The result: changing tools does not break the pattern; only changing the design system constraint breaks it.

Source: https://rottoways.com/blog/vibecoding-design-problem (read 2026-08-20)  
Source: https://uxskill.laithjunaidy.com/what-is-ai-slop.html (read 2026-08-20)  
Source: https://sailop.com/blog/ai-slop-definitive-guide-2026 (read 2026-08-20)

### 6.2 The canonical tells

Listed in order of reliability (combined from three sources):

**Colour:**
- Violet-to-indigo gradient as hero background, primary button, or accent glow. The specific Tailwind values: `from-blue-600 to-indigo-700`. The hue band 200-290 degrees. Any purple gradient with no brand justification is a tell.
- Pure white (#fff) or pure black (#000) for text. Real design uses warm or cool off-blacks (#1a1612, #141820).
- Identical `border-color` and `background-color` in cards (no contrast variation between card elements).

**Typography:**
- Inter as the only typeface from headline to footer. "The Inter problem is so widespread that simply not using Inter drops your slop score by 15-20 points." (Sailop, 2026)
- Inter, Poppins, Roboto, Montserrat, Geist, and DM Sans together account for approximately 94% of AI-generated frontend output.
- Missing `text-wrap: balance` on headings or `text-wrap: pretty` on body.
- Uniform letter-spacing across all hierarchy levels.

**Layout:**
- Three-card feature grid: `grid-cols-3 gap-6` with equal-width, identical-structure cards. The same triple pattern recurs as a three-step "how it works" and three-tier pricing table.
- Centred layout throughout with no asymmetric tension. Centred hero, centred subhead, centred body paragraphs.
- Bento grid or uniform card layout: all cards same `rounded-2xl`, same diffuse drop shadow, same visual weight regardless of content importance.
- Uniform `py-20` or `py-24` on every section.
- `max-w-7xl mx-auto` on every container.
- Section order without variation: nav, hero, features, testimonials, pricing, FAQ, CTA, footer.

**Decoration:**
- Glassmorphism: `backdrop-blur-md` navigation bar.
- Gradient "Most popular" pricing pill.
- `animate-pulse` on pricing cards.
- Terminal mockup with three coloured dots and a rounded rectangle.
- Pill badges with `bg-blue-100 text-blue-800`.
- Stock hero image under a dark scrim (`rgba(0,0,0,0.5)` overlay). The scrim is the tell.
- Sparkle or star icons to signal AI.
- Default icon set at default weight (Lucide icons in tinted circles).
- DiceBear avatar fallbacks.
- Five-star testimonial rows.

**Animation:**
- Intersection-observer reveal: `opacity: 0` + `translateY(20px)` + `ease-in-out`. Appears in approximately 83% of AI-generated landing pages.
- Linear stagger intervals (every child delayed by exactly 0.1s).
- No `:active` states on buttons (only `:hover`).
- No `prefers-reduced-motion` guard.

**Copy:**
- Marketing copy with no specific feature named. Noun phrases like "powerful platform" or "seamless experience."
- Centred eyebrow badge above the `<h1>`.

### 6.3 MIZAN's natural protection

Because MIZAN's design system commits to: a dark navy foundation, AE Gold as the only accent, Noto Kufi Arabic and Roboto as mandated typefaces, and an institutional aesthetic rather than a marketing aesthetic, most of the above tells are automatically excluded. The risk is residual: in component-level decisions (buttons, badges, icon choices, card layout) the default behaviour of any code-generation tool will still pull toward the corpus mean. The designer must specify explicit constraints at the component level.

---

## 7. Sources not found and honest gaps

**Dubai Government design system:** A search for a Dubai-specific government design system (distinct from the UAE federal DLS) returned no public-facing design system publication. The Dubai Smart Government and Dubai Digital Authority do not appear to have published a design system equivalent to the federal DLS. If MIZAN is being judged by a federal panel, the federal DLS governs; if Dubai-specific standards apply, they would need to be obtained from the relevant authority directly. This document cannot fill that gap with a generalisation.

**UAE Government Charter for Future Services (design requirements):** The DLS references this charter as a compliance target. The charter itself was not read for this document; only the DLS's description of it. The charter may contain additional design requirements not surfaced here.

**Arabic government register conventions:** No authoritative published source was found specifying which Arabic register (formal Modern Standard Arabic versus Gulf colloquial Arabic) is appropriate for federal government digital services, or which typographic conventions distinguish government registry text from general administrative text. The safe choice, consistent with the DLS's selection of Noto Kufi Arabic, is Modern Standard Arabic in a formal register.

**Existing MIZAN user research:** No user research has been conducted on the civil servant population who will use MIZAN. All patterns here are transferred from comparable contexts. They should be tested with actual users before the product is considered validated.

**Credit decision display patterns:** A search for how credit bureau scores or FICO-style ratings are displayed to non-expert recipients returned descriptions but no published design standards from a regulating body. The GRADE framework (clinical evidence quality) and the food hygiene scheme are better-documented analogues.

---

## 8. Ten rules for the designer building this product tomorrow

These rules are traceable to sources above. The weight column reflects whether a rule is mandated or constitutes strong practice.

| # | Rule | Weight | Source |
|---|---|---|---|
| 1 | Use Noto Kufi Arabic for Arabic body text and Alexandria for Arabic headings. Use Roboto for English body. These are not stylistic choices; they are mandated typefaces. | Mandatory | UAE DLS, designsystem.gov.ae/guidelines/typography |
| 2 | Set a minimum body size of 16px (1rem) and a line-height of 1.5 for all paragraph text in both languages. This is a WCAG 1.4.12 requirement, not a preference. | Mandatory | UAE DLS accessibility guideline; WCAG 2.1 |
| 3 | All interactive controls must have a touch target of at least 44 x 44px including surrounding spacing. This applies to every button, link, and form control in the submission and evaluation screens. | Strong practice (WCAG AAA 2.5.5) | USWDS button and search accessibility tests |
| 4 | Do not validate form fields on blur. Validate on submit. Show errors in an Error Summary at the top of the page, move focus to it, prefix the page title with "Error: ", and show inline messages adjacent to each failing field. Preserve everything the user typed. | Strong practice | GOV.UK Design System validation pattern |
| 5 | For directional control in bilingual screens, use `dir` attributes in HTML markup. Set `dir="rtl"` on the `<html>` element for Arabic views. Wrap Latin-script identifiers (model names, version strings) inside Arabic text with `<span dir="ltr">`. | Mandatory for correctness | W3C i18n Working Group, i18n-html-tech-bidi |
| 6 | In Arabic text, place the percent sign to the left of the number (٪١٢ not ١٢٪) and currency symbols to the left of the number. Do not mirror media controls, graphs, circular progress indicators, or clocks. | Mandatory for correctness | W3C Arabic Layout Requirements |
| 7 | The certificate must visually distinguish between "verdict determined by statistical confidence bound" and "verdict determined by exhausting available evidence." Use a qualitative label anchored to a plain-language explanation, not a confidence interval as the primary signal. A pattern like the GRADE evidence quality label (High / Moderate / Low / Insufficient evidence) is more widely understood than a percentage confidence interval. | Product requirement | Medical decision-support research; EU AI Act analysis |
| 8 | The confirmation state after submission must include a reference number, a clear statement of what happens next and when, and a way to save a record. These are the minimum elements of a GOV.UK confirmation page and match the expectations of civil servants familiar with government digital services. | Strong practice | GOV.UK confirmation pages pattern |
| 9 | Use UAE Gold exclusively on dark (navy) surfaces. Never use gold as text on a light background: the measured contrast ratio is 2.06:1 on light surfaces, which fails WCAG AA. This is documented in MIZAN's existing design system contract and corroborated by the UAE DLS guidance on core palette contrast. | Mandatory | MIZAN Design System Contract (docs/DESIGN_SYSTEM.md); UAE DLS colour-system |
| 10 | Specify explicit component-level constraints before any code generation: the named typefaces, the specific colour tokens, the layout primitives (no three-column symmetric grids, no full-gradient buttons, no uniform border-radius on all surfaces). The convergence patterns of AI-generated interfaces will emerge at the component level even when the overall design system is correct. A constraint set is more durable than a post-generation correction pass. | Strong practice | Rottoways (2026-05); UXSkill (2026-06); Sailop (2026-04) |
