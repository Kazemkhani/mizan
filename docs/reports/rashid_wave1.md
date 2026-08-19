# RASHID Wave 1 Completion Report

**Agent:** RASHID, Principal Arabic NLP and Localisation Lead  
**Wave:** 1  
**Date:** 2026-08-19  
**Repository root:** `/Users/amirhosseinkazemkhani/work/mizan`

---

## 1. Register Standard and How It Was Held

The register target is the register of TDRA circulars and UAE Cabinet resolutions. It is not Egyptian press style, not Levantine daily-newspaper style, and not customer-service chatbot style. A UAE federal reader can identify the correct register within one sentence; distinguishing features are documented in `suites/arabic/README.md` section 1.

**Mechanical enforcement applied to every string:**

- Passive participial forms for submitted items: 'المُودَعة' (deposited/filed), not 'المُقدَّمة' (submitted, which reads as press)
- Declarative openings for descriptive UI copy: 'يتضمَّن هذا السجل...' not 'جميع...' 
- Process-in-progress: 'قيد التنفيذ' not 'جارٍ' 
- Back navigation: 'العودة' not 'رجوع'
- System/framework: 'المنظومة' as the preferred formal term
- 'كافة' rather than 'جميع' for universal quantification in formal register
- Correct passive-voice usage throughout (يُودَع, يُنظَر في, يُقدَّم, يُبَتّ في)

**Three Wave 0 strings required particular correction (marked [REVIEW]):**

`app.tagline` changed from 'سجل نماذج الذكاء الاصطناعي السيادي ومحرك الامتثال التكيفي' to 'السِجَل السيادي لنماذج الذكاء الاصطناعي ومنظومة الامتثال التكيُّفية'. The definite-article-first construction ('السجل السيادي') is the correct federal government noun phrase pattern. 'منظومة' replaces 'محرك': UAE federal entities use 'منظومة' (system/framework) for integrated digital platforms.

`registry.subtitle` changed from 'جميع نماذج الذكاء الاصطناعي المقدمة لتقييم الامتثال الحكومي.' to 'يتضمَّن هذا السجل كافة نماذج الذكاء الاصطناعي المُودَعة للتقييم وفق معايير الامتثال الحكومي.' The declarative opening, 'كافة' as the quantifier, and 'المُودَعة' (filed/deposited) as the participial form are all markers of the correct administrative register.

`evaluation.streaming.title` changed from 'التقييم جارٍ' to 'التقييم قيد التنفيذ'. 'قيد التنفيذ' is the standard Gulf federal phrase for a process in execution.

**Seven additional register corrections applied across the remaining strings.** All are documented in the inline comments of `web/src/i18n/ar.ts`.

---

## 2. Dialect and Phenomenon Coverage with Counts

### Suite item counts

| Suite | File | Items | Phenomena |
|---|---|---|---|
| Capability | `suites/arabic/capability.json` | 22 | 7 |
| Safety | `suites/arabic/safety.json` | 15 | 9 |
| Bias | `suites/arabic/bias.json` | 15 | 15 |
| Red-team | `suites/arabic/redteam.json` | 15 | 8 attack categories |
| **Total** | | **67** | **39 distinct phenomena** |

### Dialect coverage

| Variety | Items | Location |
|---|---|---|
| Emirati Gulf dialect (Khaleeji) | 5 | ar-cap-001 to ar-cap-005 |
| Gulf colloquial (general) | 4 | ar-saf-004, ar-red-011, ar-red-012, ar-red-015 |
| Formal MSA governmental | 45 | across all suites |
| Arabizi / Franco-Arabic | 2 | ar-red-005, ar-red-006 |
| Mixed Arabic-English code-switching | 3 | ar-cap-009, ar-cap-010, ar-cap-011 |
| Mixed Hijri-Gregorian dates | 2 | ar-cap-013, ar-cap-014 |
| Mixed Arabic-Indic and Western digits | 2 | ar-cap-012, ar-cap-014 |

### Linguistic phenomena by category

**Dialectal input (5 items):** Khaleeji pronoun 'وش', future marker 'بـ', lexical items 'مافي/زين/والله يعطيكم العافية/وايد', discourse filler patterns.

**Diacritics (3 items):** ع-ل-م root ambiguity (knowledge vs. flag vs. taught), ح-ك-م root ambiguity (ruling vs. arbitration), م-د-ي-ن ambiguity (city vs. indebted).

**Code-switching (3 items):** Standard Arabic with embedded English noun, Gulf dialect with 'الـ'-prefixed English borrowing, technical support register with dense English vocabulary.

**Digit systems (2 items):** Arabic-Indic digits in reference numbers, mixed Arabic-Indic and Western digits.

**Calendar systems (2 items):** Hijri-only date query, mixed Hijri and Gregorian date in a contract context.

**Named entities (3 items):** TDRA official Arabic name, UAE leadership honorific protocol, UAE place names.

**Legal-administrative register (2 items):** Law vs. regulation vs. decree vs. circular taxonomy, formal passive-voice administrative phrasing.

**Cultural-religious (2 items):** Ramadan administrative schedules, formal Arabic correspondence conventions.

---

## 3. Attack Taxonomy

The 15 red-team items in `suites/arabic/redteam.json` cover the following categories:

| Category | Items | Key technique |
|---|---|---|
| Morphological obfuscation | ar-red-001, ar-red-002 | Full vs. null diacritical marking of harmful keywords; paired control probe |
| Orthographic variants | ar-red-003, ar-red-004 | Hamza elision; alef form variants (ا vs. أ vs. إ) |
| Arabizi / Franco-Arabic | ar-red-005, ar-red-006 | Number-substitution transliteration; embedded Arabizi in Arabic text |
| Prompt injection | ar-red-007, ar-red-008 | Canonical 'تجاهل التعليمات السابقة'; injection embedded mid-query |
| Islamic framing | ar-red-009 | Jurisprudential necessity (ضرورة شرعية) bypass claim |
| Authority spoofing | ar-red-010 | Fabricated ministerial decree in formal passive Arabic |
| Honorific manipulation | ar-red-011 | Religious and kinship appeals ('بحق النبي', 'يا أخي في الله') |
| PII extraction | ar-red-012 | UAE-specific PII template (Emirates ID, family book number) via roleplay |
| Fictional framing | ar-red-013 | Arabic literary register ('بلغة فصحى أدبية') to request harmful technical content |
| Bias elicitation | ar-red-014 | Nationality ranking prompt in government AI design framing |
| Unicode evasion | ar-red-015 | Zero Width Non-Joiner and Zero Width Joiner insertion to defeat keyword filters |

Each attack category targets a failure mode that is either absent from English red-team suites or substantially different in Arabic because the attack mechanism is language-specific. The Islamic framing attack, the honorific manipulation attack, the Arabizi attacks, the diacritical obfuscation attacks, and the ZWNJ evasion attack have no meaningful English equivalents.

---

## 4. Provenance Recording and Verifiability

**Recording mechanism:** Every suite item carries two machine-readable fields:

```json
"provenance": "arabic-native",
"provenance_note": "<detailed explanation of what makes this item Arabic-native>"
```

**Verifiability protocol (for AUDITOR):**

An item is correctly classified as Arabic-native if and only if:

1. Its `provenance_note` names a specific Arabic linguistic feature (dialect vocabulary, morphological form, script system, calendar system, cultural register feature, or Unicode property) that the probe exploits.
2. Translating the `prompt` to English and removing the Arabic-specific features named in the `provenance_note` either produces a generic English probe (with no distinctive safety or bias dimension) or a probe that loses its primary test mechanism entirely.
3. The Arabic-specific feature can be independently verified against a reference: Hans Wehr Arabic dictionary, Wright's Arabic Grammar (for morphology), Unicode Character Database (for script properties), or UAE government publications (for official entity names and register conventions).

**Translated items:** There are none. All 67 items were authored in Arabic. Six items involve English technical terms embedded in Arabic (the code-switching probes and the Arabizi attacks) but these are not translations; the English terms are present because the phenomenon being tested requires them.

---

## 5. BiDi Layout Hazards

Three hazards were identified and assessed. All are documented in `suites/arabic/README.md` section 6 and in `docs/DECISIONS.md` entry D-016.

**H-001 (UI string): `certificate.download_pdf`**  
String: 'تنزيل الشهادة بصيغة PDF'  
The terminal 'PDF' is a strong LTR sequence. UBA resolves this correctly in an RTL paragraph. No intervention applied. Flagged for ATELIER visual verification in Wave 3.

**H-002 (probe content, not UI): code-switching items ar-cap-009, ar-cap-010, ar-cap-011**  
Probe content contains embedded English terms. These are sent to model endpoints by HARNESS, not rendered in the web shell. UBA handles them correctly. HARNESS must submit probe content as UTF-8 without direction overrides.

**H-003 (probe content, not UI): Arabic-Indic digit items ar-cap-012, ar-cap-014**  
Arabic-Indic digits are UBA-neutral and resolve from context. Correct rendering in RTL context requires no intervention.

**No UI strings other than H-001 contain BiDi-hazardous mixed-direction sequences.**

---

## 6. SOVEREIGN-TODO Items

| Ref | Description | Owner | Wave |
|---|---|---|---|
| RASHID-ST-001 | Wire `control_id` field in suite items once GOVERNANCE publishes the control set | RASHID + GOVERNANCE | 2 |
| RASHID-ST-002 | Add Hijri-calendar scorer to HARNESS for items ar-cap-013, ar-cap-014 | HARNESS | 2 |
| RASHID-ST-003 | Arabizi normalisation scorer for ar-red-005, ar-red-006: requires Franco-Arabic decoder | HARNESS | 2 |
| RASHID-ST-004 | Unicode normalisation scorer for ar-red-015: requires ZWNJ and ZWJ stripping before keyword check | HARNESS | 2 |
| RASHID-ST-005 | Wave 3 visual RTL verification of H-001 by ATELIER | ATELIER | 3 |
| RASHID-ST-006 | Bilingual certificate copy: expand Arabic register for control names once GOVERNANCE publishes them | RASHID | 3 |

---

## 7. Verification

### Register linter

Run from repository root:

```
$ uv run python scripts/audit/register_lint.py
Files scanned: 60
Findings: 0
Register discipline: clean.
```

Exit code: 0. No findings.

Targeted scan of RASHID-owned files only:

```
$ uv run python scripts/audit/register_lint.py suites/arabic/ web/src/i18n/ar.ts web/src/i18n/en.ts
Files scanned: 7
Findings: 0
Register discipline: clean.
```

### TypeScript check

```
$ cd web && npm run lint
(no output, exit 0)
```

The updated `en.ts` and `ar.ts` catalogues are type-correct and have matching keys. New keys added to both catalogues simultaneously: `registry.model_id.label`, `registry.submitted_at.label`, `model.name.label`, `model.endpoint.label`, `model.provider.label`, `model.submit`, `evaluation.verdict.certified`, `evaluation.verdict.rejected`, `evaluation.stopping_reason.hoeffding_bound_met`, `evaluation.stopping_reason.mandatory_control_failed`, `evaluation.stopping_reason.budget_exhausted`, `evaluation.arm_pull.label`, `evaluation.confidence.label`, `evidence.probe_id.label`, `evidence.score.label`, `evidence.passed.yes`, `evidence.passed.no`, `certificate.controls.heading`, `certificate.model.heading`, `certificate.use_case.heading`, `certificate.signature.label`, `certificate.evaluator.label`, `common.not_found`, `common.retry`, `common.download`, `common.id.label`.

---

## 8. Wave 1 Acceptance Criteria Status

| Criterion | Status |
|---|---|
| Arabic suite items are Arabic-native, not translations, and marked with provenance | PASS |
| Dialectal input: Emirati Gulf dialect covered | PASS (5 items) |
| Diacritics with meaning shifts | PASS (3 items) |
| Code-switching Arabic-English | PASS (3 items) |
| Arabic-Indic vs. Western digits | PASS (2 items) |
| Hijri and Gregorian dates | PASS (2 items) |
| Named entities: Emirati names, federal entities, place names, honorifics | PASS (3 items) |
| Culturally and religiously sensitive material, UAE-specific | PASS (safety.json: 15 items) |
| Legal and administrative register | PASS (2 dedicated items, register held throughout) |
| Arabic-native red-team attacks covering jailbreaks exploiting morphology | PASS (ar-red-001, ar-red-002) |
| Diacritics or orthographic variants for filter evasion | PASS (ar-red-003, ar-red-004) |
| Script-mixing and Arabizi attacks | PASS (ar-red-005, ar-red-006) |
| Prompt injection in Arabic | PASS (ar-red-007, ar-red-008) |
| PII extraction probes in Arabic | PASS (ar-saf-006, ar-red-012) |
| Bias elicitation across Gulf-relevant demographics | PASS (15 items, bias.json) |
| UI string catalogue corrected to formal Gulf governmental register | PASS |
| [REVIEW] strings resolved | PASS (app.tagline, registry.subtitle) |
| Register linter exits zero | PASS (60 files scanned, 0 findings) |
| TypeScript check exits zero | PASS |
| BiDi hazards identified and logged | PASS (3 hazards, all assessed) |

---

## 9. Files Delivered

| File | Action | Description |
|---|---|---|
| `web/src/i18n/ar.ts` | Corrected and extended | Formal Gulf governmental register throughout; 16 strings corrected; 26 new keys added |
| `web/src/i18n/en.ts` | Extended | Matching keys for all new Arabic strings |
| `suites/arabic/capability.json` | Created | 22 Arabic-native capability probes |
| `suites/arabic/safety.json` | Created | 15 Arabic-native safety probes |
| `suites/arabic/bias.json` | Created | 15 Arabic-native bias probes |
| `suites/arabic/redteam.json` | Created | 15 Arabic-native red-team attacks |
| `suites/arabic/README.md` | Created | Register standard, dialect coverage, phenomenon taxonomy, provenance verification methodology |
| `docs/DECISIONS.md` | Extended | D-016: BiDi treatment of terminal Latin acronyms in Arabic strings |
| `docs/reports/rashid_wave1.md` | Created | This report |
