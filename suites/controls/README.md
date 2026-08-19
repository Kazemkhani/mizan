# MIZAN Control Register

**Owner:** GOVERNANCE, MIZAN Wave 1
**Version:** 1.0
**Date:** 2026-08-19

---

## Contents of this directory

| File | Purpose |
|---|---|
| `controls.json` | The master control register: all 36 controls with full provenance, pass criteria, and evidence types. |
| `use_cases.json` | Five government use cases with per-control mandatory/advisory classification, weights, and confidence thresholds. |
| `model_card_schema.json` | Extended model card schema (Mitchell et al. 2019 + UAE governance and PDPL fields). |
| `datasheet_schema.json` | Extended datasheet schema (Gebru et al. 2021 + UAE governance and PDPL fields). |
| `certificate_content.json` | Certificate assertions in English and Arabic at the level of legal precision required for government use. |
| `README.md` | This document. |

---

## How provenance is recorded

Every control in `controls.json` carries the following provenance fields:

**`framework_clause`:** The authoritative citation for the control. Values take one of two forms:

1. A verified framework reference, citing a specific named principle or article from a published UAE governance document:
   - `UAE-ETHICS-2022:PrincipleName` -- UAE AI Ethics Principles and Guidelines, December 2022, issued by the UAE Ministry of State for Artificial Intelligence. Principles cited: Fairness, Accountability, TransparencyExplainability, Privacy, RobustnessSafetyCybersecurity, HumanCentredDesign, Sustainability, TraceabilityAuditability.
   - `UAE-CHARTER-2024:PrincipleName` -- UAE Charter for the Development and Use of Artificial Intelligence, June 2024, issued by the UAE Office for Artificial Intelligence, Digital Economy and Remote Work Applications. Principles cited by name as verified from independent secondary sources.
   - `PDPL-2021:ArtN` -- Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data, with a specific article number. Article numbers for Articles 3, 4, 6, 7, 10, 12-17, and 21 were verified from a detailed secondary analysis of the law.

2. A MIZAN-defined control identifier: `MIZAN-CTL-NNN`. This signals that the control operationalises a published principle but the specific testable criterion is MIZAN-defined rather than directly enumerated in any published document. Every MIZAN-CTL-NNN entry also carries a `derives_from` field stating which published principle it operationalises and why.

**`provenance_type`:** Either `"framework_cited"` (the control maps directly to a named published principle or article) or `"mizan_defined"` (the control operationalises a published principle with MIZAN-defined criteria).

**`derives_from`:** Populated only when `provenance_type` is `"mizan_defined"`. States the published principle(s) from which the control is derived and the reasoning for treating it as MIZAN-defined rather than framework-cited.

---

## How a MIZAN-defined control differs from a framework-cited one

The UAE AI Governance Framework at the federal level is published as principles rather than as an enumerated testable control catalogue. The UAE AI Ethics Principles and Guidelines (December 2022) and the UAE Charter for the Development and Use of Artificial Intelligence (June 2024) both name principles and provide brief descriptions, but neither provides clause-level testable criteria (e.g. specific pass thresholds, probe methodologies, or measurement definitions).

Where a principle directly implies a testable requirement and MIZAN's operationalisation is substantially the same as what the principle states, the control is classified as `framework_cited`. For example, the UAE AI Ethics Guide Robustness, Safety and Cybersecurity principle explicitly mentions "adversarial attacks, resilience, fallback procedures"; a control requiring prompt injection resistance and citing this principle is `framework_cited`.

Where MIZAN must define specific criteria that go beyond what the principle states (for example, a specific Arabic language quality threshold, or a specific government-domain hallucination rate measurement), the control is classified as `mizan_defined` and assigned a MIZAN-CTL-NNN identifier. This distinction is honest: it tells a government evaluator exactly which requirements derive from published authority and which are MIZAN's reasoned operationalisation.

---

## How to verify any claim made in this register

**To verify a UAE-ETHICS-2022 citation:**
- The UAE AI Ethics Principles and Guidelines (December 2022) was issued by the UAE Ministry of State for Artificial Intelligence. The primary PDF is hosted at `https://ai.gov.ae/wp-content/uploads/2023/03/MOCAI-AI-Ethics-EN-1.pdf` (note: this URL returned HTTP 403 at time of research on 2026-08-19; alternative: `https://u.ae/-/media/AI-publications/MOCAI-AI-Ethics-EN-1.pdf`, which returned HTTP 404 at time of research). Principle names and descriptions were verified from secondary sources: regulations.ai (`https://regulations.ai/regulations/RAI-AE-NA-AEPGUXX-2022`, retrieved 2026-08-19) and digital.nemko.com (`https://digital.nemko.com/regulations/uae-ai-regulations`, retrieved 2026-08-19). If a verifier can access the primary PDF (e.g. via an institutional connection to `ai.gov.ae`), they should confirm the eight principles named in this register against the primary source.

**To verify a UAE-CHARTER-2024 citation:**
- The UAE Charter for the Development and Use of Artificial Intelligence was issued in June 2024 by the UAE Office for Artificial Intelligence, Digital Economy and Remote Work Applications. The principle names cited in this register were verified from two independent secondary sources: securiti.ai (`https://securiti.ai/uae-charter-for-the-development-and-use-of-ai/`, retrieved 2026-08-19) and megatek.ai (`https://megatek.ai/en/regulation/uae-charter-for-the-development-and-use-of-artificial-intelligence/`, retrieved 2026-08-19). The official primary document is available via `https://u.ae`. Note: neither secondary source confirmed an official numerical ordering of the twelve principles; principles are cited by name in this register to avoid asserting a numbering that cannot be verified.

**To verify a PDPL-2021 citation:**
- Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data. Official Arabic text available via `https://u.ae/en/about-the-uae/digital-uae/data/data-protection-laws`. Article numbers for Articles 2, 3, 4, 6, 7, 10, 12-17, and 21 were verified from securiti.ai (`https://securiti.ai/uae-personal-data-protection-law/`, retrieved 2026-08-19). Cross-border transfer provisions are confirmed as existing in the PDPL; however, the specific article number was not confirmed from available secondary sources and is the subject of SOVEREIGN-TODO G-003.

**To verify a MIZAN-CTL citation:**
- MIZAN-defined controls are not derived from a published external document and require no external verification. Their justification is in the `derives_from` field of each control record in `controls.json`. The reasoning may be challenged by any reviewer; the appropriate response is to either update the `derives_from` field or reclassify the control.

---

## MIZAN-defined controls summary

| MIZAN-CTL ID | Control ID | Control Name | Derives From |
|---|---|---|---|
| MIZAN-CTL-001 | ctrl-fnd-003 | Equal Service Quality Across Languages | UAE-CHARTER-2024:AlgorithmicBiasMitigation applied to language dimension |
| MIZAN-CTL-002 | ctrl-pdp-006 | PII Non-Leakage under Adversarial Probing | PDPL-2021:Art3 + UAE-ETHICS-2022:RobustnessSafetyCybersecurity |
| MIZAN-CTL-003 | ctrl-pdp-004 | Cross-Border Data Transfer Control | PDPL-2021 cross-border provisions (article number unconfirmed; SOVEREIGN-TODO G-003) |
| MIZAN-CTL-004 | ctrl-acr-003 | Government-Claim Hallucination Rate | UAE-ETHICS-2022:RobustnessSafetyCybersecurity applied to factual hallucination in government-domain claims |
| MIZAN-CTL-005 | ctrl-lca-001 | Arabic Language Accuracy | UAE National AI Strategy 2031 Arabic AI pillar; UAE-CHARTER-2024:InclusiveAccess |
| MIZAN-CTL-006 | ctrl-lca-002 | Cultural Sensitivity Compliance | UAE-CHARTER-2024:HumanCommitment; UAE-CHARTER-2024:InclusiveAccess |
| MIZAN-CTL-007 | ctrl-lca-003 | Islamic Values Respect | UAE-CHARTER-2024:HumanCommitment (human values in UAE constitutional context) |
| MIZAN-CTL-008 | ctrl-lca-004 | UAE Formal Government Register Compliance | UAE-CHARTER-2024:GovernanceAccountability |

---

## Arabic string review policy

Fields in this control register marked `"rashid_review_required": true` require review and approval by RASHID (Principal Arabic NLP and Localisation Lead) before the control set is considered final. These fields are written to the best formal Arabic standard achievable without native Gulf governmental expertise, and marked to enable RASHID to identify and correct any register, vocabulary, or register issues without having to scan the entire file.

Arabic fields in this register that are not marked `rashid_review_required` have been written in formal Modern Standard Arabic and are considered acceptable for Wave 1 delivery pending RASHID's Wave 1 review.

Do not treat any Arabic field in this register as final until RASHID has signed off on Wave 1.

---

## Control domain summary

| Domain | Control IDs | Count |
|---|---|---|
| Safety and Harm Refusal | ctrl-shr-001 to ctrl-shr-004 | 4 |
| Fairness and Non-Discrimination | ctrl-fnd-001 to ctrl-fnd-003 | 3 |
| Transparency and Explainability | ctrl-tre-001 to ctrl-tre-004 | 4 |
| Human Oversight | ctrl-hov-001 to ctrl-hov-003 | 3 |
| Privacy and Personal Data | ctrl-pdp-001 to ctrl-pdp-006 | 6 |
| Security and Adversarial Robustness | ctrl-sar-001 to ctrl-sar-004 | 4 |
| Accuracy and Reliability | ctrl-acr-001 to ctrl-acr-004 | 4 |
| Accountability and Auditability | ctrl-aca-001 to ctrl-aca-004 | 4 |
| Linguistic and Cultural Appropriateness | ctrl-lca-001 to ctrl-lca-004 | 4 |
| **Total** | | **36** |

---

## Provenance split

| Provenance type | Count | Percentage |
|---|---|---|
| Framework-cited (UAE-ETHICS-2022, UAE-CHARTER-2024, PDPL-2021) | 28 | 78% |
| MIZAN-defined (MIZAN-CTL-001 to MIZAN-CTL-008) | 8 | 22% |

---

## SOVEREIGN-TODO items in this domain

| Reference | Description | Resolution path |
|---|---|---|
| G-001 | Primary PDF of UAE AI Ethics Principles and Guidelines (Dec 2022) was not accessible at time of research. Principle names verified from secondary sources only. | Obtain primary document via institutional access and verify principle names and any sub-clause structure against primary. Update `sources_consulted` in controls.json. |
| G-002 | Official numerical ordering of UAE Charter 2024 principles not confirmed. Principles cited by name. | Obtain primary Charter document and confirm any official numbering. If official numbering exists, update framework_clause references from name-based to number-based form. |
| G-003 | Specific PDPL article number for cross-border transfer provisions not confirmed from available secondary sources. MIZAN-CTL-003 used. | Obtain legal review from a UAE-qualified legal practitioner. If article number confirmed, update ctrl-pdp-004 framework_clause from MIZAN-CTL-003 to PDPL-2021:Art[N]. |
| G-004 | Certificate validity period not yet defined. | Consult with TDRA on appropriate validity period for government AI certificates. Log decision in DECISIONS.md under D-GOV-004. |
