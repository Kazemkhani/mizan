# Contributing to MIZAN

This repository runs on one rule, and everything below is a consequence of it.

> **An exit code is a claim. The command and its output are the evidence.**

Every production defect this project has recorded was the same shape: a property asserted in a document with nothing executable behind it. Append-only written in a comment with no database trigger behind it. A contrast ratio measured against a background the interface never renders. A typeface named in a design system that the offline build could not load. An Arabic refusal detector that could not detect the most common formal Arabic refusal.

None of those were caught by reading more carefully. Each was caught by a script that recomputed the claim from the artefact. Write that script.

## Set up a clean checkout

Install the exact committed Python and interface dependency sets:

```bash
uv sync --frozen --extra dev
(cd web && npm ci)
```

The `dev` extra is required for the test and audit commands below. Do not use
an unlocked install when reporting a reproducibility result.

## Before you open a pull request

Run every gate and paste the real, unpiped output into the description. Not a summary of it, and not an assurance that it passed.

```bash
make test
python3 scripts/audit/register_lint.py
python3 scripts/audit/verify_contrast.py
python3 scripts/audit/verify_grounding.py
uv run python scripts/verify_evidence.py
```

Beware the pipe. `some_command | tail -5; echo $?` reports the exit status of `tail`, not of the command you care about. That mistake has already produced one false audit finding here.

## House rules

**British English.** Everywhere, including code comments and commit messages. Enforced as rule E003.

**No em-dashes and no emojis.** Enforced as rules E001 and E002. Ticks and arrows are permitted in comments and documents, and banned in user-facing strings, where a tick becomes a checkmark bullet.

**Precise language on anything a reader outside the team will see.** Name the action, name the outcome, name the safeguard. Rule E005 rejects marketing register, an efficiency claim with no number in the same sentence, and any statement that the system uses AI without saying what the AI does. MIZAN is described as a registry, an engine, a certificate, an instrument, or infrastructure, and as nothing else.

**Every number is sourced.** A figure must be produced by a committed script, attributed to a named official source with the date it was read, or labelled an assumption on the same surface where it appears. An unsourced figure is treated as equal to a fabricated benchmark. Enforced as gate G3.

## Things that will be rejected

Tuning a scorer, a threshold or a keyword list until a model passes. A scorer that is wrong must be corrected; that is a different act from a scorer that is inconvenient. If a model does not pass, fix the model.

Evaluation flakiness absorbed by a retry. Fix the cause. A retry that is genuinely correct behaviour, such as optimistic concurrency on a hash-chain append, must say so in a comment and be tested.

A test that asserts nothing. A guard clause tested against an empty table is not tested at all: a `BEFORE DELETE` trigger that never fires looks exactly like a trigger that does not exist.

Silent failure. A fallback that makes a dead source look alive is worse than an error. State what the system does when a dependency is unavailable, make that behaviour visible, and test it.

An invented dataset, an invented control, or an invented citation. Where the source cannot be reached, record what is needed in `docs/DATA_REQUESTS.md`. An honest gap is acceptable. A plausible-looking fabrication is not.

## Editing the gates

The gates live in `scripts/audit/` and they are deliberately outside the reach of the work they measure. A component that can edit the gate it is measured by is not gated.

Gates do get things wrong, and when one does the remedy is a test plus a fix, never a suppression. Several exemptions already exist because the gate was wrong rather than the work: dingbats in comments, HTML attributes in documents, verbatim government data that must not be corrected into British English. Each carries a test pinning the exemption so it cannot widen quietly. Propose gate changes in a pull request of their own.

## Evidence and the database

The `evidence` table is append-only, enforced by database triggers and a per-evaluation hash chain. Never issue `UPDATE` or `DELETE` against it.

`mizan.engine.db.database.append_evidence()` is the only sanctioned write path. It serialises the payload canonically, computes the hash itself and sets the chain link, so a caller cannot supply a hash. Raw `INSERT` is prohibited and the triggers will reject it.

The same applies to issued certificates: identity and verdict fields are immutable after issuance.

## Determinism

Fixed seed in, identical output out, on any machine. Seed every source of randomness explicitly and never rely on a global. A random identifier inside a hashed payload will break reproducibility silently, which has happened here once already.

Any determinism test needs a companion asserting that a different seed produces different output, or the first test can pass while measuring nothing.

## Documentation

Record consequential choices in `docs/DECISIONS.md`, with the reasoning and the alternatives rejected. Take the next free number and check the file first, because parallel contributors have collided on numbering before.

Risks belong in `docs/RISKS.md`, each with a named mitigation. A risk without a mitigation is an excuse.

## Contribution licence

Unless you state otherwise, a contribution intentionally submitted for
inclusion in MIZAN is provided under the Apache License 2.0, as described in
section 5 of [`LICENSE`](LICENSE). Mark material that you do not intend as a
contribution explicitly and do not submit third-party material without its
licence and required attribution.
