# Engineering provenance

MIZAN retains the reports produced during its staged, AI-assisted build. They
show how requirements were decomposed, how specialist review roles challenged
the implementation and how findings were closed with executable evidence.

This record is kept because a polished final tree alone does not show which
claims failed review, which alternatives were rejected or which checks found
their own false positives.

## Role labels in historical files

Names such as `BANDIT`, `GOVERNANCE`, `HARNESS`, `SENTINEL`, `RASHID`, `BAYAN`,
`ATELIER`, `ARCHITECT` and `AUDITOR` identify functional workstreams in the
build process. They are not claims that MIZAN employed a human team of that
size, or that a named external expert approved the work.

The historical material is grouped as follows:

- `docs/reports/` records subsystem completion reports and reviewer responses;
- `docs/audit/` records adversarial findings, signoffs and corrections;
- `docs/design/` records interface research and visual review; and
- `docs/evidence/` contains measurements and their reproducible inputs.

## How to read the record

Historical reports describe the repository at the commit state when they were
written. Test counts, file locations and open findings can become stale. The
current source of truth is:

1. [`../README.md`](../README.md) for the product and reproducible entry points;
2. [`CHARTER.md`](CHARTER.md) for scope and non-negotiable principles;
3. [`ROADMAP.md`](ROADMAP.md) for current readiness and remaining work;
4. [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`DECISIONS.md`](DECISIONS.md) for
   implementation boundaries; and
5. [`RISKS.md`](RISKS.md) for known limitations and mitigations.

When a historical report conflicts with current code or one of these documents,
the current code and current source-of-truth document win. The older report is
not silently rewritten because its original state is part of the audit trail.

## What this provenance does and does not prove

The record demonstrates an engineering method: scoped roles, independent review,
reproducible checks and explicit correction. It does not by itself demonstrate
regulatory approval, independent certification, native-language expert review,
production security or fitness for a particular government deployment.

Those boundaries are intentional. External review should be attributed only
when the reviewer, scope, release and resulting findings can be named.
