# Third-party notices

MIZAN's source code and original documentation are licensed under the
[Apache License 2.0](LICENSE). The materials below are not relicensed under
Apache-2.0. Their original terms continue to apply.

## UAE open government data

The cached datasets in `suites/data/` are licensed under the
[Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/).
CC BY 4.0 requires appropriate credit, a link to the licence and an indication
of whether changes were made. No attribution below implies endorsement of
MIZAN by a publisher or portal operator.

### UAE Open Data / Bayanat

- **Material:** *Population by Sex and District*
- **Publisher:** Federal Competitiveness and Statistics Centre
- **Source:** [Bayanat dataset page](https://bayanat.ae/en/Datasets/Dataset-info?id=dPUU00NDddAHkifXrsla0cLfS_C0eMcaC-yK_jbnCOQ)
- **Terms:** [UAE Open Data Terms of Use](https://opendata.fcsc.gov.ae/p/terms-of-use)
- **Changes:** MIZAN parsed the server-rendered HTML preview tables and
  serialised them as JSON. The cache contains five preview rows from each of
  six resources. Field values were not substantively altered.

### Ajman Open Data Portal

The following datasets were published through the Ajman Open Data Portal.
The portal's [terms and conditions](https://data.ajman.ae/terms/terms-and-conditions/)
state that its open datasets are available under CC BY 4.0.

| Material | Publisher | Source | MIZAN cache and changes |
|---|---|---|---|
| *Human Resources Department Systems and Policies Data* | Department of Human Resources, Ajman | [Dataset](https://data.ajman.ae/explore/dataset/byanat-alanzmh-walsyasat-bdaerh-almward-albshryh/) | All 27 records retrieved through the portal API and serialised as JSON; field values were not substantively altered. |
| *Benefit Certificates for Rent Contracts* | Municipality & Planning Department, Ajman | [Dataset](https://data.ajman.ae/explore/dataset/benefit-certificates-for-rent-contracts/) | All 105 records retrieved through the portal API and serialised as JSON; field values were not substantively altered. |
| *Number of reports, security certificates and initiatives of Al Hamidiya Comprehensive Police Station Statistics* | Ajman Police | [Dataset](https://data.ajman.ae/explore/dataset/number-of-reports-security-certificates-and-initiatives-of-al-hamidiya-comprehen/) | All 39 records retrieved through the portal API and serialised as JSON; field values were not substantively altered. |
| *List of All Re-Export COO (Certificate of Origin) in 2023 (Part 2)* | Ajman Chamber | [Dataset](https://data.ajman.ae/explore/dataset/coo-re-export-2023-part-2/) | The first 100 of 56,975 records retrieved through the portal API and serialised as JSON; field values were not substantively altered. |
| *Speed Centre services names and fees* | Transport Authority, Ajman | [Dataset](https://data.ajman.ae/explore/dataset/speed-center-services-names-and-fees/) | All 60 records retrieved through the portal API and serialised as JSON; field values were not substantively altered. This cache is retained as a secondary reference and is not a primary use-case binding. |

Dataset-specific provenance, read dates, content hashes and cache extents are
recorded in each `suites/data/*.manifest.json` file and in
[`docs/evidence/data_sources.md`](docs/evidence/data_sources.md).

## Typefaces

The typefaces under `web/public/fonts/` use a separate licence:
SIL Open Font License 1.1. The complete licence and copyright notice for each
family is stored beside the font files.

| Family | Copyright holder | Licence file |
|---|---|---|
| Alexandria | Copyright 2022 The Alexandria Project Authors | [`LICENSE-alexandria.txt`](web/public/fonts/LICENSE-alexandria.txt) |
| Noto Kufi Arabic | Copyright 2019-2022 Google LLC | [`LICENSE-noto-kufi-arabic.txt`](web/public/fonts/LICENSE-noto-kufi-arabic.txt) |
| Roboto | Copyright 2011 The Roboto Project Authors | [`LICENSE-roboto.txt`](web/public/fonts/LICENSE-roboto.txt) |

## Dependency licences

Python and JavaScript dependencies are not vendored into the source
distribution. Their own licences govern installation and use. The locked
dependency sets are recorded in `uv.lock` and `web/package-lock.json`.
