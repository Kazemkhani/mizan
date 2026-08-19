# Arabic Suite Documentation

**Owner:** RASHID, Principal Arabic NLP and Localisation Lead  
**Wave:** 1  
**Repository path:** `suites/arabic/`

---

## 1. Register Standard

All Arabic content in this suite is in **formal Gulf governmental register**. The reference register is that of TDRA circulars, UAE Cabinet resolutions, and Federal National Council communications. It is not Egyptian or Levantine press style, and it is not customer-service chatbot style.

The distinction is material and mechanically verifiable. Specific markers of the correct register:

| Feature | Gulf governmental (correct) | Levantine/Egyptian press (wrong) |
|---|---|---|
| Sentence opening | 'يتضمَّن هذا السجل...' | 'يحتوي على...' |
| Passive participle for submitted items | 'المُودَعة' | 'المُقدَّمة' |
| Process in progress | 'قيد التنفيذ' | 'جارٍ التنفيذ' |
| Formal request phrase | 'يُرجى التكرم بـ' | 'من فضلك' |
| Verdict | 'صدر القرار' | 'اتُّخِذ القرار' |
| Back navigation | 'العودة' | 'رجوع' |
| System/framework | 'المنظومة' | 'النظام' (acceptable but less formal) |

A UAE federal reader fluent in government Arabic can identify the register difference within one sentence. Strings that read as Egyptian press or chatbot register are incorrect for this product and constitute a findings by AUDITOR.

---

## 2. Dialect Coverage

The suite covers the following Arabic varieties:

| Variety | Suite file | Item count |
|---|---|---|
| Emirati Gulf dialect (Khaleeji) | capability.json | 5 items (ar-cap-001 to ar-cap-005) |
| Gulf colloquial (general) | safety.json, redteam.json | 4 items across files |
| Formal MSA governmental | capability.json, safety.json, bias.json | 28 items |
| Arabizi / Franco-Arabic | redteam.json | 2 items (ar-red-005, ar-red-006) |
| Mixed Arabic-English code-switching | capability.json | 3 items (ar-cap-009, ar-cap-010, ar-cap-011) |
| Mixed Hijri-Gregorian | capability.json | 2 items (ar-cap-013, ar-cap-014) |

---

## 3. Phenomenon Taxonomy

Items are tagged by `phenomenon`. The full taxonomy:

### Linguistic phenomena
- `dialectal_input_gulf_emirati` -- Khaleeji-specific vocabulary, pronouns, future marker
- `diacritics_semantic_shift` -- words whose meaning changes under different diacritical marking
- `code_switching_arabic_english` -- mid-sentence switching with UAE-specific borrowing patterns
- `arabic_indic_digits` -- Arabic-Indic numeral system in government reference numbers
- `hijri_gregorian_dates` -- Hijri calendar dates and mixed Hijri-Gregorian formats
- `named_entity_federal_institution` -- UAE federal entity names requiring exact Arabic forms
- `named_entity_emirati_honorifics` -- UAE leadership protocol and correct honorific formulas
- `named_entity_place_names` -- UAE emirate and government office place names
- `legal_administrative_register` -- formal passive-voice government Arabic
- `cultural_religious_sensitivity` -- culturally calibrated responses for UAE/Gulf context
- `formal_salutation_and_closure` -- UAE government correspondence conventions
- `mixed_digit_systems_in_administrative_context` -- Arabic-Indic and Western digits in same field

### Safety phenomena
- `religious_fatwa_request` -- request for Islamic legal ruling from AI
- `religious_legal_ruling_request` -- Sharia legal advice framing
- `harmful_content_formal_msa` -- harmful request in formal Arabic to test register-dependent safety
- `harmful_content_gulf_dialect` -- same harmful request in Gulf dialect (paired probe)
- `drug_content_gulf_slang` -- Gulf Arabic narcotic vocabulary
- `pii_extraction_government_context` -- PII request in government employee framing
- `political_sensitivity_uae` -- inter-emirate and federal authority queries
- `culturally_sensitive_gender_gulf` -- gender service queries in UAE cultural context
- `harmful_content_government_framing` -- harmful technical request in procurement language
- `religious_incitement_risk` -- queries that could elicit sectarian content
- `scam_assistance_request_arabic` -- government impersonation fraud assistance
- `workplace_harassment_guidance_request` -- constructive dismissal guidance request
- `cybercrime_facilitation_request` -- surveillance evasion framing
- `self_harm_crisis_arabic` -- crisis expression in Gulf dialect
- `misinformation_government_claim` -- false government policy premise

### Bias phenomena
- `nationality_bias_uae` -- UAE national vs. expatriate service priority
- `migrant_labour_status_bias` -- domestic workers vs. professionals
- `gender_bias_gulf_context` -- gender in UAE government AI service
- `religious_identity_bias` -- Muslim vs. non-Muslim service recipients
- `tribal_affiliation_bias_uae` -- Bani Yas and UAE tribal affiliation
- `economic_class_bias` -- wasta and wealth-based queue-jumping
- `language_proficiency_bias` -- Arabic vs. non-Arabic speaker assistance
- `age_bias_digital_services` -- elderly user framing
- `educational_background_bias` -- education level differential
- `visa_residency_status_bias` -- tourist service access
- `occupational_bias` -- manual worker service access
- `political_opinion_elicitation` -- model political opinion on UAE government
- `national_origin_employment_bias` -- Emiratisation vs. discrimination
- `private_vs_public_sector_bias` -- sector-based service differential
- `disability_status_bias` -- People of Determination service access

### Attack phenomena
- `full_tashkeel_to_evade_filter` -- diacritical obfuscation to bypass keyword filters
- `undiacritised_control_probe` -- control for diacritics-dependent safety gap
- `hamza_elision_attack` -- hamza omission to evade high-risk keyword detection
- `alef_form_variant_attack` -- alef form variants to obfuscate keywords
- `arabizi_franco_arabic_attack` -- Latin-script Arabic with number substitutions
- `arabizi_code_switch_attack` -- embedded Arabizi harmful keyword in Arabic text
- `arabic_system_prompt_injection` -- canonical Arabic 'ignore previous instructions'
- `arabic_injection_embedded_in_legitimate_query` -- injection hidden in plausible query
- `religious_permission_claim_to_bypass_safety` -- Islamic jurisprudence bypass claim
- `fake_government_decree_override` -- fabricated ministerial decree authority claim
- `excessive_religious_honorific_appeal` -- emotional/religious social engineering
- `pii_extraction_via_arabic_roleplay` -- UAE-specific PII request in roleplay
- `arabic_novelist_jailbreak` -- Arabic literary register fictional framing
- `nationality_hierarchy_elicitation` -- nationality ranking prompt
- `zero_width_non_joiner_evasion` -- invisible Unicode character insertion

---

## 4. Item Counts by Suite

| Suite file | Items | Phenomena covered |
|---|---|---|
| `capability.json` | 22 | 7 distinct phenomena |
| `safety.json` | 15 | 9 distinct phenomena |
| `bias.json` | 15 | 15 distinct phenomena |
| `redteam.json` | 15 | 8 distinct attack categories |
| **Total** | **67** | **39 distinct phenomena** |

---

## 5. Provenance Standard and Verification

Every item carries two provenance fields:

- `"provenance": "arabic-native"` -- the item was designed in Arabic, not translated from English
- `"provenance_note"` -- a detailed explanation of what makes the item Arabic-native, specifically what phenomenon it targets that cannot be replicated by translating an English probe

**How to verify provenance:**

1. For dialectal items: locate the Khaleeji-specific vocabulary or grammatical structure named in the `provenance_note`. A UAE national or a qualified Gulf Arabic linguist can confirm these are dialect-specific forms.

2. For diacritical items: the `provenance_note` names the specific diacritical ambiguity. Any Arabic morphology reference (e.g. Hans Wehr dictionary, Wright's Arabic Grammar) confirms the semantic shift described.

3. For code-switching items: the `provenance_note` identifies the Arabic-specific borrowing pattern. The code-switch point (which terms remain in English) is culturally determined and cannot be generated by translating an English source.

4. For red-team attacks: the `provenance_note` names the Arabic script or morphology feature exploited. Each attack can be independently verified against the Unicode Bidirectional Algorithm specification, the Unicode Character Database, or Arabic orthography references as applicable.

**AUDITOR finding: translated item presented as native.** AUDITOR is instructed to treat any item presented as Arabic-native that can be shown to be a word-for-word translation of a known English probe as a critical finding. The test: an item is not Arabic-native if its `prompt` is equivalent to a standard English probe after translation, and if removing the Arabic-specific features from the `provenance_note` leaves nothing distinctive. All items in this suite would, after translation to English, either become a generic English probe (for the content type) or lose their distinctive safety or bias dimension entirely.

---

## 6. BiDi Layout Hazards

The following string-level BiDi concerns were identified during Wave 1. All are flagged for ATELIER's visual verification in Wave 3.

### H-001: `certificate.download_pdf`

**String:** `'تنزيل الشهادة بصيغة PDF'`  
**Hazard:** The terminal LTR sequence 'PDF' in an RTL string.  
**UBA resolution:** In an RTL paragraph, UBA renders the visual order as [PDF] [بصيغة] [الشهادة] [تنزيل], reading right to left. The Arabic text is visually coherent; PDF appears at the visual left (logical end in RTL). This is the correct Arabic typographic convention for a terminal acronym.  
**Recommendation:** No intervention required unless ATELIER's Wave 3 visual review shows unexpected rendering. Do not apply `unicode-bidi: bidi-override` or `direction: ltr` overrides.

### H-002: Code-switching probe strings in `capability.json`

**Items:** ar-cap-009, ar-cap-010, ar-cap-011 (probes sent to models under test, not UI strings)  
**Hazard:** These contain embedded English terms ('update', 'support', 'deadline', 'portal', 'system', 'error', 'login'). They are probe content, not UI strings, so they are not rendered in the web shell. HARNESS is responsible for sending them correctly to model endpoints.  
**Recommendation:** HARNESS must submit probe content as UTF-8 with no BOM and no direction override. UBA will handle mixed-direction probe text correctly at the receiving model endpoint.

### H-003: Arabic-Indic digits in `capability.json`

**Items:** ar-cap-012, ar-cap-014 (probe content only)  
**Hazard:** Arabic-Indic digits (٣٤٥٦٧٨) are classified as neutral by UBA and resolve directionally from context. Within an RTL probe string, they will render correctly.  
**Recommendation:** No intervention. Document for AUDITOR's reference.

---

## 7. SOVEREIGN-TODO Items

| Ref | Description | Owner | Wave |
|---|---|---|---|
| RASHID-ST-001 | Wire `control_id` field in suite items once GOVERNANCE publishes the control set | RASHID + GOVERNANCE | 2 |
| RASHID-ST-002 | Add Hijri-calendar scorer to HARNESS for ar-cap-013 and ar-cap-014 | HARNESS | 2 |
| RASHID-ST-003 | Arabizi normalisation scorer for ar-red-005 and ar-red-006: requires a Franco-Arabic decoder | HARNESS | 2 |
| RASHID-ST-004 | Unicode normalisation scorer for ar-red-015: requires ZWNJ/ZWJ stripping before keyword check | HARNESS | 2 |
| RASHID-ST-005 | Wave 3 visual RTL verification of H-001 by ATELIER | ATELIER | 3 |
| RASHID-ST-006 | Bilingual certificate copy: expand Arabic register for control names once GOVERNANCE publishes them | RASHID | 3 |

---

## 8. Relationship to SENTINEL's Red-Team Probe Engine

SENTINEL owns the probe engine and the English-language attack design. This Arabic suite provides the Arabic-native attack items that SENTINEL's engine dispatches. SENTINEL must not translate this suite's items back to English for engine processing; the Arabic-language probes must be submitted to model endpoints as written.

The `attack_category` field in `redteam.json` aligns with SENTINEL's taxonomy. RASHID and SENTINEL must agree on any changes to that taxonomy before Wave 2.
