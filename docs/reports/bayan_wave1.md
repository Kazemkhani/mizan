# BAYAN Wave 1 Completion Report

**Agent:** BAYAN, Open-Data Integration Lead  
**Mandate:** Charter Addendum 01, section 2  
**Date:** 2026-08-19  
**Status:** All five use cases bound and hash-verified. All gates pass.

---

## 1. Dataset Bindings

All five MIZAN use cases are bound to real, fetched, hash-verified datasets from the Ajman
Open Data Portal (data.ajman.ae). The Ajman portal is authorised by the charter's network
exception. The Bayanat portal (bayanat.ae) is inaccessible from unauthenticated server-side
HTTP calls; the full failure record and operator instructions are in section 4 and in
`docs/DATA_REQUESTS.md`.

| Use Case | Dataset Name as Published | Publisher | Dataset GUID | Read Date | Records Cached | Cache SHA-256 (first 16) |
|----------|--------------------------|-----------|--------------|-----------|---------------|--------------------------|
| uc-001 | Speed Centre Services Names and Fees | Ajman Government / Speed Centre | da_vx5h92 | 2026-08-19 | 60 of 60 | e45ea5cbf1def0e5 |
| uc-002 | بيانات الانظمة والسياسات بادارة الموارد البشرية | Ajman Government | da_f8z46q | 2026-08-19 | 27 of 27 | 2d51e8b9a40e3989 |
| uc-003 | Benefit Certificates for Rent Contracts | Ajman Government | da_hq5ypb | 2026-08-19 | 100 of 105 (sample) | 2b348a15b703f187 |
| uc-004 | Number of Reports, Security Certificates and Initiatives | Ajman Government / Al Hamidiya Police | da_mew4ks | 2026-08-19 | 39 of 39 | f82db3681c31e262 |
| uc-005 | COO Re-Export 2023 Part 2 | Ajman Government / Ajman Chamber | da_isigsw | 2026-08-19 | 100 of 56975 (sample) | 7b771a2b397bfca1 |

Full binding documentation including portal URLs, API URLs, licence terms, last-modified
dates, and grounding rationale is in `docs/evidence/data_sources.md`.

Cache files and manifests are in `suites/data/`. Each dataset has three files:
`{id}.json` (cache), `{id}.meta.json` (full API metadata), `{id}.manifest.json` (binding
record with GUID and read date).

---

## 2. Hash Verification: Live Fetches Matching Committed Caches

Live fetch output on 2026-08-19 (unpiped, verbatim):

```
BAYAN Dataset Fetch and Verify
Mode: LIVE fetch and hash comparison
Cache directory: /Users/amirhosseinkazemkhani/work/mizan/suites/data
========================================================================
[PASS] uc-001  speed-center-services-names-and-fees
       Status: OK
       live and cache agree. Compared 60 records. Normalised content SHA-256: cda50d98be77ae13. Portal total: 60.

[PASS] uc-002  byanat-alanzmh-walsyasat-bdaerh-almward-albshryh
       Status: OK
       live and cache agree. Compared 27 records. Normalised content SHA-256: d37e11e907372462. Portal total: 27.

[PASS] uc-003  benefit-certificates-for-rent-contracts
       Status: OK
       live and cache agree. Compared 100 records. Normalised content SHA-256: 693e6ba5f50392db. Portal total: 105.

[PASS] uc-004  number-of-reports-security-certificates-and-initiatives
       Status: OK
       live and cache agree. Compared 39 records. Normalised content SHA-256: 66ff968b4e1c8bb3. Portal total: 39.

[PASS] uc-005  coo-re-export-2023-part-2
       Status: OK
       live and cache agree. Compared 100 records. Normalised content SHA-256: 553fc1c31b05eaac. Portal total: 56975.

========================================================================
Datasets checked: 5
Failures: 0
Result: all live fetches match their committed caches.
```

**Comparison method:** For each dataset, the script fetches up to 100 records from the
portal, parses the JSON response, and normalises it using order-independent per-record
serialisation (`json.dumps(sorted([json.dumps(r, sort_keys=True) for r in records]))`).
It computes SHA-256 of the normalised string from both the live fetch and the committed
cache, then compares. The normalised content hash printed above is this comparison hash,
not the raw file hash. Both sides produce the same value, proving the committed cache
is a faithful copy of what the portal serves.

For full-corpus datasets (uc-001, uc-002, uc-004), every record is compared. For
large datasets (uc-003 at 105 records, uc-005 at 56,975 records), 100 representative
records are compared (the first 100 in portal order), which is what was committed.

---

## 3. Failure Behaviour and Test Evidence

### Stated failure behaviour (`agents/data/fetch_datasets.py`, lines 14-26)

Three failure modes, all visible and all cause exit code 1:

- **FETCH_FAILED:** The script prints the exception, states the offline cache SHA-256
  (so the operator can find it), explicitly states the cache was NOT used as a substitute,
  and continues to the next dataset. The final exit code is 1. A network outage never
  silently degrades to cached results.

- **HASH_MISMATCH:** Both the live normalised hash and the cache normalised hash are
  printed. The script states the portal dataset has changed. Exit code 1. The operator
  knows exactly what to do: inspect the change and recommit the cache if appropriate.

- **CACHE_MISSING:** The path is printed. Exit code 1.

The offline cache is never silently accepted as a substitute for a live fetch. A dead
source that looks alive is the defect this script exists to prevent.

### Failure detection test

Conducted on 2026-08-19 by corrupting the uc-001 cache
(`speed-center-services-names-and-fees.json`, field `service_fees` of record 0 set to
`CORRUPTED_FOR_FAILURE_TEST`), running the script, then restoring the original from backup.

Output (verbatim, exit code 1):

```
BAYAN Dataset Fetch and Verify
Mode: LIVE fetch and hash comparison
Cache directory: /Users/amirhosseinkazemkhani/work/mizan/suites/data
========================================================================
[FAIL] uc-001  speed-center-services-names-and-fees
       Status: HASH_MISMATCH
       content mismatch for speed-center-services-names-and-fees. Live normalised SHA-256:
       cda50d98be77ae13. Cache normalised SHA-256: 78545534536a1426. Portal reports 60
       total records; cache holds 60 records. The portal dataset has changed since the
       cache was committed. Re-run the fetch script to update the cache.

[PASS] uc-002  byanat-alanzmh-walsyasat-bdaerh-almward-albshryh
...
Datasets checked: 5
Failures: 1
Result: FAIL. One or more datasets could not be verified. See details above. The offline
cache must not be treated as authoritative until the live fetch succeeds.
```

The two hashes differ, both are printed, exit code is 1. No silent fallback occurred.

---

## 4. Data Requests Log (`docs/DATA_REQUESTS.md`)

Six requests are open. All six block on the same root cause (DR-001).

### DR-001: Bayanat REST API access (blocks all five Bayanat bindings)

**Root cause:** The bayanat.ae portal is a Sitecore SPA. Every REST API endpoint returns
HTTP 302 to `/en/error/404` from unauthenticated server-side calls. The SPA generates
`.AspNetCore.Antiforgery.*` tokens in the browser; curl and urllib cannot obtain them.

**Endpoints tried (all returned 302):**
- `https://bayanat.ae/api/Dataset/GetAll?pageNo=1&pageSize=10&lang=en`
- `https://bayanat.ae/api/DatasetResources/GetDatasetResource?resourceID=test`
- `https://bayanat.ae/api/DatasetResources/GetAll?pageNo=1&pageSize=10`
- `https://bayanat.ae/api/Dataset/GetDatasets?pageNo=1&pageSize=20&topic=Government&subTopic=Service%20Centers`

**What the operator must do:** Open a browser, navigate to `https://bayanat.ae/en/Datasets`,
search for the dataset, open its Resource Information page, copy the Resource GUID
(UUID format), fetch the resource at
`https://bayanat.ae/api/DatasetResources/GetDatasetResource?resourceID={GUID}`,
save the response to `suites/data/bayanat-{slug}.json`, and commit alongside a manifest
with the GUID and read date. Then update `docs/evidence/data_sources.md`.

### DR-002 through DR-006: Dataset requests per use case

| DR | Use Case | What is Needed | Why |
|----|----------|----------------|-----|
| DR-002 | uc-001 | Citizen transaction volumes by service and language (FCSC or TDRA on bayanat.ae) | Supplements Speed Centre fees with request frequency and language-mix data |
| DR-003 | uc-002 | Federal document type inventory (circulars, policies, decisions) with Arabic titles | Broadens the 27-record Ajman policy corpus to federal scale |
| DR-004 | uc-003 | Social benefit categories and eligibility criteria across UAE (MoCD or GPSSA) | Extends the single-type Ajman rent certificate dataset to the full benefit taxonomy |
| DR-005 | uc-004 | Emirate-wide or federal incident class distribution (not single-station) | Makes the evaluation class distribution more representative than one police station |
| DR-006 | uc-005 | Federal procurement contracts or budget expenditure by category (MoF or GAGP) | Grounds the full procurement lifecycle beyond trade document field structure |

Resource GUIDs for DR-002 through DR-006 are not yet known; operator must retrieve from
the Resource Information page as described in DR-001.

---

## 5. Certificate Field Change Required from GOVERNANCE

**File:** `suites/controls/certificate_content.json`  
**Owner:** GOVERNANCE agent (BAYAN must not edit this file)

**Gap:** The `mandatory_fields_on_certificate_face` array does not contain a field for
dataset GUIDs consulted during the evaluation. A certificate that does not name the
datasets used to calibrate and verify the evaluation is not auditable: a verifier
cannot confirm that the stated grounding is real without knowing which datasets were
consulted.

**Field to add:**

```json
{
  "field_id": "dataset_guids_consulted",
  "label_en": "Dataset GUIDs Consulted",
  "label_ar": "معرفات البيانات المستشار بها",
  "description": "One or more dataset GUIDs from the MIZAN binding registry that were used to calibrate or verify the evaluation controls for this use case. Each GUID identifies a specific dataset on a UAE government open data portal. A verifier can retrieve the dataset by its GUID and confirm that the evaluation weights and control thresholds are grounded in real government data, not in invented numbers."
}
```

**Placement:** After `evidence_bundle_hash` in the mandatory fields list (it is a
provenance field, adjacent to the other provenance anchors).

**Impact:** Without this field, a certificate states that MIZAN evaluates AI models
against UAE government data but does not name that data. The addendum section 3 requires
that every binding carry a dataset name, publisher, URL, GUID, and read date. The
certificate is the trust anchor for the whole system; if it does not propagate the GUID,
the provenance chain is broken at the final output.

---

## 6. Gate Outputs

### G1/G2/G3 grounding gates

Command: `python3 scripts/audit/verify_grounding.py`

```
MIZAN Data Grounding and Honesty Gates
============================================================
G1 risks                 PASS
G2 dataset bindings      PASS
G3 sourced numbers       PASS


Findings: 0
Grounding: every gate passes.
```

### Register lint gate

Command: `python3 scripts/audit/register_lint.py`

```
Files scanned: 97
Findings: 0
Register discipline: clean.
```

---

## 7. Files Delivered

| File | Purpose |
|------|---------|
| `agents/data/__init__.py` | BAYAN workstream package marker |
| `agents/data/fetch_datasets.py` | Live fetch, hash verification, failure detection |
| `suites/data/speed-center-services-names-and-fees.json` | uc-001 cache (60 records) |
| `suites/data/speed-center-services-names-and-fees.meta.json` | uc-001 portal metadata |
| `suites/data/speed-center-services-names-and-fees.manifest.json` | uc-001 binding manifest with GUID da_vx5h92 |
| `suites/data/byanat-alanzmh-walsyasat-bdaerh-almward-albshryh.json` | uc-002 cache (27 records) |
| `suites/data/byanat-alanzmh-walsyasat-bdaerh-albshryh.meta.json` | uc-002 portal metadata |
| `suites/data/byanat-alanzmh-walsyasat-bdaerh-albshryh.manifest.json` | uc-002 binding manifest with GUID da_f8z46q |
| `suites/data/benefit-certificates-for-rent-contracts.json` | uc-003 cache (100 of 105 records) |
| `suites/data/benefit-certificates-for-rent-contracts.meta.json` | uc-003 portal metadata |
| `suites/data/benefit-certificates-for-rent-contracts.manifest.json` | uc-003 binding manifest with GUID da_hq5ypb |
| `suites/data/number-of-reports-security-certificates-and-initiatives.json` | uc-004 cache (39 records) |
| `suites/data/number-of-reports-security-certificates-and-initiatives.meta.json` | uc-004 portal metadata |
| `suites/data/number-of-reports-security-certificates-and-initiatives.manifest.json` | uc-004 binding manifest with GUID da_mew4ks |
| `suites/data/coo-re-export-2023-part-2.json` | uc-005 cache (100 of 56975 records) |
| `suites/data/coo-re-export-2023-part-2.meta.json` | uc-005 portal metadata |
| `suites/data/coo-re-export-2023-part-2.manifest.json` | uc-005 binding manifest with GUID da_isigsw |
| `docs/evidence/data_sources.md` | Full binding documentation for all five use cases |
| `docs/DATA_REQUESTS.md` | Six open requests for Bayanat datasets with operator instructions |
| `docs/reports/bayan_wave1.md` | This report |

---

## 8. Note for AUDITOR

The file `mizan/engine/bandit/allocator.py` contains the American spelling "labelled"
in a comment (line inspected during lint runs; outside BAYAN's ownership scope and
therefore not corrected). AUDITOR should verify whether this file is excluded from the
lint gate or whether a finding is expected.

---

*BAYAN Wave 1 complete. All five use cases bound. All gates pass. GOVERNANCE action
required on dataset_guids_consulted field. Bayanat operator actions documented in
`docs/DATA_REQUESTS.md`.*
