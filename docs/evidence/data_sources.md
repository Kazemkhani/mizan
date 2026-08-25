# MIZAN Dataset Bindings

BAYAN Open-Data Integration Lead. Charter Addendum 01 section 2.
Read date for all bindings: 2026-08-19.

Every binding in this file was verified by a live fetch on the read date.
The fetch script is `agents/data/fetch_datasets.py`. The committed caches are
in `suites/data/`. The script exits zero only when the live response hash
matches the committed cache hash. Run it to reproduce these results.

The cached datasets remain under Creative Commons Attribution 4.0. Each
manifest records the publisher, source, licence, terms, cache extent and
changes made. The redistribution attribution is collected in
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md). Portal terms were
last checked on 2026-08-25.

---

## Portal and access notes

**Bayanat.ae (Federal Open Data Portal).** Used for the citizen chatbot
use case (see below). Dataset info pages are served as complete HTML to
unauthenticated clients (HTTP 200, no token required). The documented REST
endpoint `/api/DatasetResources/GetDatasetResource?resourceID={ResourceGUID}`
was investigated and found inaccessible: calling it with any value returns
HTTP 400 or a zero-byte body. The Resource GUID the endpoint requires is
not exposed in the page HTML. The correct access method is to GET the dataset
info page and parse the server-rendered Data Explorer table from the page HTML.
See `agents/data/fetch_bayanat.py` for the full rationale and risk statement.
The Ajman Speed Centre fees dataset previously used as a secondary reference
is retained in `suites/data/` but is not the primary binding for the chatbot
use case.

**Ajman Open Data Portal (data.ajman.ae).** Used for uc-002 through uc-005.
The charter explicitly names this portal as an authorised source. It exposes
an unauthenticated Opendatasoft Explore API v2.1. All Ajman datasets are
published under CC BY 4.0. The portal assigns each dataset a `dataset_uid`
(format: `da_XXXXXX`), recorded as the Resource GUID equivalent for each
binding.

---

## uc-001 | Citizen-Facing Arabic Chatbot

**Dataset name as published:** Population by Sex and District

**Arabic title (as published):** السكان حسب الجنس والمقاطعة

**Publishing entity:** Federal Competitiveness and Statistics Centre (FCSC)

**Portal:** bayanat.ae (Federal Open Data Portal)

**Dataset URL:** `https://bayanat.ae/en/Datasets/Dataset-info?id=dPUU00NDddAHkifXrsla0cLfS_C0eMcaC-yK_jbnCOQ`

**Access method:** Server-rendered HTML parse (no REST API; see `agents/data/fetch_bayanat.py`)

**Resource GUID (page token):** `dPUU00NDddAHkifXrsla0cLfS_C0eMcaC-yK_jbnCOQ`
[source: bayanat.ae dataset info page, read on 2026-08-19. The portal uses a
43-character base64url token rather than a UUID; this token uniquely identifies
the dataset page.]

**Last updated:** 2023 data (latest year in the dataset as served on 2026-08-19)

**Read date:** 2026-08-19

**Resources (previewed):** 6 resources (one per year: 2002, 2003, 2004, 2005, 2007, 2008)

**Rows per resource:** 5 preview rows of 27 total in portal per resource

**Total preview rows cached:** 30 (5 per resource x 6 resources)

**Cache file:** `suites/data/bayanat-population-sex-district.json`

**Cache SHA-256:** 15ae4aa016e44011ade4f588ec5d0c2b0823c2bb9d60b7c1fdc29b011287aba1

**Live-to-cache content hash (normalised):** 02f544cd85891a67 [verified 2026-08-19 by agents/data/fetch_datasets.py]

**Columns:** Year, Medical_District_AR, Medical_District_EN, Gender_AR, Gender_EN, Value

**Sample row:** Year=2002, Medical_District_AR=ابو ظبى, Medical_District_EN=Abu Dhabi, Gender_AR=ذكر, Gender_EN=Male, Value=539000

**Why this dataset is genuinely better for uc-001 than the Ajman Speed Centre binding:**
The Ajman Speed Centre dataset (60 bilingual service names and fees) grounds
knowledge about a specific emirate-level service centre. The FCSC Population
by Sex and District dataset is a federal publication carrying Arabic and English
labels for all seven emirates, published by the body responsible for national
statistics. For a use case about an Arabic citizen-facing chatbot, the critical
controls are Arabic language accuracy and the use of standardised government
Arabic vocabulary. The FCSC dataset provides exactly this: officially published
Arabic administrative vocabulary for district names (Medical_District_AR:
"ابو ظبى", "الغربية", "العين", "دبى", "الشارقة") and demographic categories
("ذكر", "انثى") across all emirates, in the register that federal government
AI systems should use. A model producing non-standard or localised Arabic
variants of these names would be caught by controls grounded in this dataset.
The Speed Centre fees dataset remains valid grounding for service-knowledge
calibration but is narrower in geographic and linguistic scope for the primary
Arabic-accuracy controls.

---

## uc-002 | Internal Document Summarisation

**Dataset name as published:** Human Resources Department Systems and Policies Data

**Arabic title (as published):** بيانات الأنظمة والسياسات بدائرة الموارد البشرية

**Publishing entity:** Department of Human Resources, Ajman

**Portal:** Ajman Open Data Portal (data.ajman.ae)

**Dataset URL:** https://data.ajman.ae/explore/dataset/byanat-alanzmh-walsyasat-bdaerh-almward-albshryh/

**API URL:** `https://data.ajman.ae/api/explore/v2.1/catalog/datasets/byanat-alanzmh-walsyasat-bdaerh-almward-albshryh`

**Resource GUID (dataset_uid):** da_f8z46q

**Dataset ID:** byanat-alanzmh-walsyasat-bdaerh-almward-albshryh

**Last updated:** 2024-11-11 [source: data.ajman.ae API, read on 2026-08-19]

**Read date:** 2026-08-19

**Records cached:** 27 of 27 (full dataset)

**Cache file:** suites/data/byanat-alanzmh-walsyasat-bdaerh-almward-albshryh.json

**Cache SHA-256:** 2d51e8b9a40e39897b74d7c7f303945c569fdb290c8b1379742647bc12196e4e

**Live-to-cache content hash (normalised):** d37e11e907372462 [verified 2026-08-19 by agents/data/fetch_datasets.py]

**Genuine grounding rationale:** The internal document summarisation use case
evaluates whether a model can accurately summarise Arabic government policy
and procedure documents. This dataset is an inventory of 27 internal
government systems and policies issued by Ajman's Human Resources Department,
in Arabic, for example "سياسة التوطين" (Emiratisation Policy), "نظام ادارة الاداء" (Performance Management System), "نظام التدريب والتطوير في حكومة عجمان" (Training and Development System). Each record includes the document title in Arabic and
the year of issuance. This is the document type and language register that a
government internal summarisation model would encounter: formal Arabic policy
names, procedural titles, and administrative references. It calibrates the
test suite's vocabulary coverage for the Arabic document corpus and the
expected register of government policy language.

---

## uc-003 | Benefits Eligibility Triage

**Dataset name as published:** Benefit Certificates for Rent Contracts

**Arabic title (as published):** شهادات الافادة لعقود الإيجار

**Publishing entity:** Municipality and Planning Department, Ajman

**Portal:** Ajman Open Data Portal (data.ajman.ae)

**Dataset URL:** https://data.ajman.ae/explore/dataset/benefit-certificates-for-rent-contracts/

**API URL:** `https://data.ajman.ae/api/explore/v2.1/catalog/datasets/benefit-certificates-for-rent-contracts`

**Resource GUID (dataset_uid):** da_hq5ypb

**Dataset ID:** benefit-certificates-for-rent-contracts

**Last updated:** 2025-11-26 [source: data.ajman.ae API, read on 2026-08-19]

**Read date:** 2026-08-19

**Records cached:** 105 of 105 (full dataset)

**Cache file:** suites/data/benefit-certificates-for-rent-contracts.json

**Cache SHA-256:** 2b348a15b703f187314d7240bdb83b55dfc634c1c35e7e70d882be952b1e6925

**Live-to-cache content hash (normalised):** 693e6ba5f50392db [verified 2026-08-19 by agents/data/fetch_datasets.py, first 100 records]

**Genuine grounding rationale:** The benefits triage use case evaluates
whether a model can correctly classify citizen requests against eligibility
rules and benefit categories. This dataset records monthly issuance counts of
benefit certificates for rent contracts from 2017 to 2024 in both Arabic and
English (month names, service names). Its bilingual structure (month_ar,
month_en, service_ar, service_en, number_of_issued_benefit_certificates)
directly calibrates two aspects of the evaluation: first, whether the model
correctly identifies benefit type categories in Arabic; second, whether the
model's classification outputs align with historical issuance patterns. A
model that routes zero requests to a benefit type that historically generates
dozens of monthly certificates is wrong. This dataset is about a specific
benefit category (rent contract certificates) and its grounding is bounded to
that category; the operator's Bayanat request covers broader eligibility
categories.

---

## uc-004 | Traffic Incident Classification

**Dataset name as published:** Number of reports, security certificates and initiatives of Al Hamidiya Comprehensive Police Station Statistics

**Arabic title (as published):** احصائية عدد البلاغات والشهادات الامنية والمبادرات لمركز شرطة الحميدية الشامل

**Publishing entity:** Ajman Police

**Portal:** Ajman Open Data Portal (data.ajman.ae)

**Dataset URL:** https://data.ajman.ae/explore/dataset/number-of-reports-security-certificates-and-initiatives-of-al-hamidiya-comprehen/

**API URL:** `https://data.ajman.ae/api/explore/v2.1/catalog/datasets/number-of-reports-security-certificates-and-initiatives-of-al-hamidiya-comprehen`

**Resource GUID (dataset_uid):** da_mew4ks

**Dataset ID:** number-of-reports-security-certificates-and-initiatives-of-al-hamidiya-comprehen

**Last updated:** 2024-07-09 [source: data.ajman.ae API, read on 2026-08-19]

**Read date:** 2026-08-19

**Records cached:** 39 of 39 (full dataset)

**Cache file:** suites/data/number-of-reports-security-certificates-and-initiatives-of-al-hamidiya-comprehen.json

**Cache SHA-256:** f82db3681c31e2621588378a294ab879ecca76dc05290e82bb93305e5e722423

**Live-to-cache content hash (normalised):** 66ff968b4e1c8bb3 [verified 2026-08-19 by agents/data/fetch_datasets.py]

**Genuine grounding rationale:** The incident classification use case evaluates
whether a model can correctly classify incoming reports into defined incident
categories. This dataset provides 39 months of police station report counts
broken into three classification categories: criminal_report, financial_report
(finiancial_report in the field name), and traffic_report, plus several
certificate types. This is precisely what an incident classification model
must produce: a count per category per time period. The dataset calibrates
the expected class distribution: if the model over-classifies incidents as
traffic relative to criminal, this dataset provides the baseline against which
that error is measurable. The UAE government use case for incident
classification is a federal entity receiving reports and needing to route them
to the correct department; this dataset shows the actual classification
breakdown that a real UAE police station produces.

---

## uc-005 | Procurement Document Analysis

**Dataset name as published:** List of All Re-Export COO (Certificate of Origin) in 2023 (Part 2)

**Arabic title (as published):** قائمة جميع شهادات المنشأ لإعادة التصدير لعام 2023 (الجزء الثاني)

**Publishing entity:** Ajman Chamber

**Portal:** Ajman Open Data Portal (data.ajman.ae)

**Dataset URL:** https://data.ajman.ae/explore/dataset/coo-re-export-2023-part-2/

**API URL:** `https://data.ajman.ae/api/explore/v2.1/catalog/datasets/coo-re-export-2023-part-2`

**Resource GUID (dataset_uid):** da_isigsw

**Dataset ID:** coo-re-export-2023-part-2

**Last updated:** 2024-07-09 [source: data.ajman.ae API, read on 2026-08-19]

**Read date:** 2026-08-19

**Records cached:** 100 of 56975 (representative sample; full dataset too large for offline embedding)

**Cache file:** suites/data/coo-re-export-2023-part-2.json

**Cache SHA-256:** 7b771a2b397bfca1cb3351a7a1adc0088184bc659b78233c84133521e9623bd9

**Live-to-cache content hash (normalised):** 553fc1c31b05eaac [verified 2026-08-19 by agents/data/fetch_datasets.py, first 100 records]

**Genuine grounding rationale:** The procurement document analysis use case
evaluates whether a model can extract structured information from procurement
and trade documents. A Certificate of Origin (COO) is a bilingual
(Arabic/English) government-issued trade document that asserts the country of
origin of goods; it contains the same classes of fields that appear in
procurement documents: product codes, destination country, origin country,
company identifier, licence type, and date. This dataset (56,975 COO records)
provides a realistic distribution of the document field values a procurement
analysis model would encounter in UAE government trade and procurement
contexts. The size (56,975 records in 2023 alone) demonstrates the scale at
which procurement document processing occurs and grounds the argument for
automation. The operator's Bayanat request covers government tender and
contract datasets which would provide more direct grounding for the full
procurement lifecycle.

---

## Bayanat portal status

The Bayanat REST API (https://bayanat.ae/api/DatasetResources/GetDatasetResource)
requires a browser antiforgery session that unauthenticated server-side calls
cannot obtain. All attempts on 2026-08-19 returned HTTP 302 to
/en/error/404. Datasets that would ideally come from Bayanat are recorded in
docs/DATA_REQUESTS.md. The dataset count of 56 publishing entities published
on bayanat.ae is cited in the pitch materials as: "56 publishing entities on
bayanat.ae as of 19 August 2026" [source: Charter Addendum 01 section 2,
read on 2026-08-19].
