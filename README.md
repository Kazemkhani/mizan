<div align="center">

# MIZAN · ميزان

**A sovereign registry, an adaptive evaluation engine, and a signed certificate for AI models entering government service.**

*Nations certify aircraft before they fly and medicines before they ship. No equivalent authority exists for AI models entering government service. MIZAN is that authority, rendered as infrastructure.*

</div>

---

## The question this answers

> How might government entities select, evaluate and deploy compliant AI models by intended use case, performance, security and regulatory requirement, aligned to the UAE National Strategy for Artificial Intelligence 2031 and the UAE AI Governance Framework?

Every artefact in this repository traces back to a clause of that question. Anything that does not serve it is not built.

## What MIZAN does

A model enters the registry. An adaptive engine adjudicates it against the exact controls its intended use case demands, buying evidence in the order that resolves the certification decision fastest. It exits with a bilingual certificate mapped control by control, where every verdict links down to the individual probe that produced it and every probe carries a `SHA-256` hash.

Three principles govern the build.

**Arabic is a first-class citizen, not a translation pass.** Evaluation suites, red-team attacks, certificates and the interface exist natively in Arabic with correct right-to-left behaviour. A model that is safe in English and unsafe in Arabic fails. This is enforced in the evidence: every Arabic suite item records `provenance: arabic-native`, and a translated item presented as native is a blocking audit finding.

**Evidence over assertion.** Every score links to the raw evidence that produced it. Evidence rows are append-only, enforced by database triggers and a per-evaluation hash chain rather than by convention, so any edit or excision is detectable by traversal. See [`docs/DECISIONS.md`](docs/DECISIONS.md) `D-011` through `D-014`.

**The system compounds.** Every completed evaluation teaches the strategy-search layer faster test orderings for that use-case class. The registry gets quicker the more it is used.

## The journey

The demonstration is one named journey, shown rather than described.

Fatima leads AI adoption at a federal entity. She submits a candidate model against the Arabic citizen-chatbot use case. She watches evaluation budget reallocate live between test suites as confidence bounds tighten. An Arabic-native safety probe fails, and she opens the exact failing exchange from the certificate trail in one click. The compliant model is then adjudicated and carries a signed certificate citing both its evidence hashes and the government datasets consulted.

## Repository structure

```
engine/db/schema.sql      Postgres-ready DDL. Immutability triggers, hash chain.
mizan/
  engine/bandit/          UCB1 allocator over test suites; sequential stopping rules
  engine/mcss/            Monte Carlo strategy search; per-use-case-class memory
  engine/db/              Data access. append_evidence() is the only sanctioned write path
  agents/harness/         Suite runners, scorers, model endpoint adapters
  agents/redteam/         Adversarial probe engine
  api/                    FastAPI service and websocket evaluation stream
agents/data/              Open-data fetch and hash verification against committed caches
suites/
  controls/               Control register, five government use cases, certificate content
  arabic/                 Arabic-native suite items and attack sets
  redteam/                Bilingual jailbreak, injection and bias probes
  data/                   Verbatim cached government datasets with manifests
web/                      React and Vite interface, bilingual with true RTL mirroring
scripts/
  audit/                  The gates. Register discipline, contrast, grounding
  prove_reduction.py      The measured proof
  verify_evidence.py      Recomputes every hash and traverses the chain
docs/
  audit/                  Wave signoffs. Adversarial, and record their own false positives
  evidence/               Every number that appears anywhere, with the run that produced it
  reports/                Per-agent completion reports
```

## Verification

Claims in this repository are executable. An exit code is a claim; the command is the evidence.

| Gate | Command | What it enforces |
|---|---|---|
| Tests | `make test` | Engine, evidence immutability, harness determinism |
| Register discipline | `python3 scripts/audit/register_lint.py` | British English, no em-dashes, no emojis, precise language |
| Contrast | `python3 scripts/audit/verify_contrast.py` | WCAG AA on every text pairing, alpha composited |
| Evidence integrity | `uv run python scripts/verify_evidence.py` | Recomputes every payload hash, traverses the chain |
| Grounding and honesty | `python3 scripts/audit/verify_grounding.py` | Risks are named with mitigations; every use case is bound to a real dataset; every pitch-facing figure is sourced |
| The proof | `uv run python scripts/prove_reduction.py` | Adaptive against exhaustive evaluation, verdict parity |

The grounding gate treats an unsourced number as a defect equal to a fabricated benchmark. A figure must be produced by a committed script, attributed to a named official source with the date it was read, or labelled an assumption on the surface where it appears.

## Data grounding

Use cases are bound to real UAE government open data rather than to invented context. Each binding records the dataset name as published, the publishing entity, the portal URL, the resource identifier and the date it was read, in [`docs/evidence/data_sources.md`](docs/evidence/data_sources.md).

Each binding is fetched live and compared by hash against a committed offline cache, so the demonstration cannot fail on venue connectivity and a reviewer can tell staleness from tampering. A hash divergence raises `HASH_MISMATCH` and exits non-zero; there is no silent fallback that would make a dead source look alive.

Where a dataset cannot be reached from the build environment, it is never invented. The request is recorded in [`docs/DATA_REQUESTS.md`](docs/DATA_REQUESTS.md) with the exact steps to retrieve it by hand.

## Getting started

Requires Python managed by `uv`, and Node for the interface.

```bash
uv sync                 # Python toolchain
cd web && npm install   # interface dependencies
make seed               # populate the registry
make dev                # API and interface together
make test               # the full suite
```

The evaluation path runs offline by design. Model endpoints resolve to deterministic mocks, and typefaces are self-hosted, so no request leaves the machine during a demonstration.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/CHARTER.md`](docs/CHARTER.md) | The engagement charter and its addendum |
| [`docs/DELIVERY_PLAN.md`](docs/DELIVERY_PLAN.md) | Build order, dependency graph, acceptance criteria per wave |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Schema, module boundaries, interface contracts |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Every consequential choice with its rationale |
| [`docs/RISKS.md`](docs/RISKS.md) | Implementation risks, each with a named mitigation |
| [`docs/audit/`](docs/audit/) | Adversarial wave signoffs |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to work in this repository |

## Status and honest limits

This is pilot-scale work. Present-tense claims describe one entity, one use case, and a ninety-day pilot. National figures appear only as labelled assumptions or as the question a pilot exists to answer. [`docs/RISKS.md`](docs/RISKS.md) states the known limits, including the point at which the evidence guarantee stops holding and what would extend it.

Controls whose provenance is a MIZAN reading of a published principle are labelled as such and are distinguished in the register from controls citing a named framework principle. That distinction is deliberate and is not smoothed over.

## Licence

Proprietary. All rights reserved. See [`LICENSE`](LICENSE), which also records the terms governing the redistributed typefaces and the cached government datasets.
