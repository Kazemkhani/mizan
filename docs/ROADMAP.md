# MIZAN roadmap

Updated: 2026-08-25

This roadmap separates what the research prototype demonstrates today from the
work required for a credible pilot. It is ordered by risk reduction, not by
visual novelty. Dates are assigned only when an accountable owner and delivery
window exist.

Repository visibility is an owner decision outside the codebase. Completing a
milestone never changes visibility by itself.

## Baseline today

The committed prototype can register a model, select a use case, run a
deterministic adaptive evaluation, preserve the resulting evidence and render a
bilingual certificate. Its default demonstration path is offline and the proof
script compares adaptive and exhaustive evaluation under the same corpus and
decision rules.

This baseline is suitable for code review and controlled demonstrations. It is
not yet a production assurance service or a regulatory certification system.

## Milestone 1: open-source baseline

Goal: make the repository safe, legible and reproducible before any visibility
change is considered.

| Gate | Evidence | State |
|---|---|---|
| Licence and third-party attribution | `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md` | Complete |
| Community and security policies | contribution, conduct, issue and security files | Complete |
| Protected default branch | pull request, signed squash and required-check rules | Complete |
| Dependency security | alerts, automated security fixes and governed routine updates | Complete |
| Reproducible environment | `uv.lock`, `package-lock.json`, pinned CI toolchain | Complete |
| Clean-checkout verification | all required commands run from a fresh checkout | Complete |
| Public documentation | charter, roadmap, architecture, risks and provenance agree | Complete |
| Demonstration media | current screenshots or recording of the actual interface | Pending |
| Maintainer approval | explicit decision after all private material is reviewed | Pending |

Exit condition: every row is complete and the repository owner separately
approves a visibility change.

## Milestone 2: evaluation validity

Goal: strengthen the evidence behind model decisions before expanding the set of
claims.

- Expand each control corpus beyond its statistical stopping requirement where
  a meaningful bounded pass is expected.
- Benchmark multiple model families and failure profiles across a declared seed
  set, publishing the full distribution rather than a best run.
- Calibrate control thresholds with documented domain reasoning and sensitivity
  analysis.
- Add regression fixtures for every scorer and malformed endpoint response.
- Commission native Arabic review of the control language, suites and
  certificate register.
- Separate framework quotation, project interpretation and testable project
  control in the machine-readable register.
- Document when exhaustive evaluation is a realistic baseline and when it is
  only a research comparison.

Exit condition: claims about reduction, parity and Arabic coverage have a
reproducible report, stated population and known confidence limits.

## Milestone 3: production security and operations

Goal: make a deployable instance defensible under an explicit threat model.

- Add identity, role-based access control and tenant boundaries.
- Move the primary deployment path to PostgreSQL with reviewed migrations,
  backup and restoration procedures.
- Replace prototype signing with asymmetric keys held outside the application
  process and publish verification instructions.
- Define evidence retention, deletion, export and personal-data handling rules.
- Add request limits, endpoint allowlists, network egress controls and audit
  logging.
- Add structured observability for evaluation state, failures and security
  events without recording confidential prompts by default.
- Threat-model the API, evidence chain, certificate verifier and live endpoint
  adapter, then remediate critical and high findings.
- Define supported versions, release signing and an incident response process.

Exit condition: the deployment runbook, recovery test, threat model and
independent security review all correspond to the same release candidate.

## Milestone 4: controlled pilot

Goal: test the operating model with a named use case and accountable human
review, without presenting the pilot as regulatory approval.

- Agree the intended use, decision owner, escalation route and success measures
  with the pilot entity.
- Validate dataset rights, data flows and retention against the pilot context.
- Run shadow evaluations before any result influences a real procurement or
  deployment decision.
- Measure reviewer agreement, unresolved-control rate, evaluation cost and time
  to evidence, with incident and override records alongside them.
- Review false passes, false failures and Arabic-specific failures with domain
  specialists.
- Publish a pilot report that separates measured outcomes, assumptions and work
  not attempted.

Exit condition: the accountable pilot owner accepts the evidence and remaining
risks for the stated use case. The result does not transfer automatically to
another model, entity or use case.

## Continuous release gates

Every milestone retains the same minimum engineering gates:

| Concern | Command |
|---|---|
| Core behaviour | `make test` |
| Interface type and production build | `cd web && npm run build` |
| Public language | `python3 scripts/audit/register_lint.py` |
| Source and risk grounding | `python3 scripts/audit/verify_grounding.py` |
| Evidence integrity | `uv run python scripts/verify_evidence.py` |
| Adaptive versus exhaustive proof | `make prove` |

A new feature does not compensate for a failed gate. A changed claim requires
changed evidence in the same pull request.

## High-value contribution areas

The most useful contributions are currently:

1. Arabic evaluation cases with native provenance and scorer coverage.
2. Statistical review of stopping rules, calibration and comparison design.
3. Certificate signature verification and key-management design.
4. Threat models and adversarial tests for evidence and endpoint boundaries.
5. Reproducible corpus expansion tied to a named control and failure mode.
6. Browser-level accessibility and RTL regression coverage.

Open an issue before large changes so the evidence requirement and product
boundary are agreed first.
