# MIZAN Delivery Plan

Principal Delivery Orchestrator. Authority: `docs/CHARTER.md`.
Repository root: `~/work/mizan`. All charter paths (`/engine`, `/agents`, `/api`, `/web`, `/suites`, `/docs`, `/scripts`) resolve relative to this root.

## 1. Mandate

Convert the Monte Carlo UCB1 engine into sovereign AI evaluation infrastructure and deliver a pitch-ready MVP for the TDRA UAE Hackathon 2026 under the theme Responsible AI and Smart Cognitive Government.

The question every artefact traces back to: enable government entities to select, evaluate and deploy compliant AI models by intended use case, performance, security and regulatory requirement, achieving an 80 percent reduction in model evaluation time and 100 percent compliance with government AI standards, aligned to the UAE National Strategy for Artificial Intelligence 2031 and the UAE AI Governance Framework.

## 2. Register discipline (enforced by AUDITOR on every wave)

British English. No em-dashes. No emojis. American spellings are a rejection. Confident, precise, governmental tone. Arabic in formal Gulf governmental register, never Levantine or Egyptian press style.

## 3. Numbers doctrine

Every quantitative claim that reaches the pitch must be produced by a committed, reproducible script with output written to `docs/evidence/`. If a measured figure falls short of target, the configuration is tuned honestly, re-measured, and the real figure reported. Fabrication or extrapolation of a pitch number terminates the engagement.

## 3A. Build order, Charter Addendum 01

Amends section 4 below. This is a dependency sequence, not a triage list. **Nothing in the charter is descoped.** No workstream may choose a lighter implementation on the assumption that time is short.

Addendum section 7, the deadline compression and freeze schedule, is struck in full by operator instruction and does not apply. Addendum sections 1 to 6 stand and win over the charter on any conflict.

The spine is built first because everything else hangs from it, then the work proceeds outward:

1. **The spine.** The Fatima journey running end to end offline in under ninety seconds, and `scripts/prove_reduction.py` producing real measured figures. Neither is meaningful without the other: a demo with no measured proof is a description, and a proof with no journey is a spreadsheet.
2. **Dataset bindings.** BAYAN binds the Arabic citizen-chatbot use case to a real Bayanat resource with a live fetch and a hash-verified offline cache, then the remaining four use cases.
3. **Certificates.** Signed bilingual PDFs, control by control, evidence hashes and dataset GUIDs present, print-perfect. One certified and one rejected.
4. **The remaining use cases.** Full adjudication paths for all five, not only the demo case.
5. **The compounding registry and the Arabic polish.** The learning curve made visible, and Arabic register brought to final quality across every surface rather than only the demo path.

Everything in the charter ships. The demo shows one journey; the rest of the system stays in the repository, finished, and comes out under questioning.

## 3B. The journey law

The demo is one named journey and it is demonstrated, never described. Fatima, AI lead at a federal entity. She submits a candidate model against the Arabic citizen-chatbot use case, watches evaluation budget reallocate live between suites, sees an Arabic-native safety probe fail and opens the exact failing question from the certificate trail, then sees the compliant model carry a signed certificate. Both models are pre-staged. The dashboard's default state, the seed data and the choreography are all built around this and nothing in the demo exists that does not serve it.

## 3C. Standing gates added by Addendum 01

| Gate | Command | Law |
|---|---|---|
| Register discipline | `python3 scripts/audit/register_lint.py` | British English, no em-dashes, no emojis, charter section 7 |
| Precise language, E005 | same command | Addendum section 4: name the action, name the outcome, name the safeguard |
| Contrast | `python3 scripts/audit/verify_contrast.py` | WCAG AA on every text pairing, composited |
| Evidence integrity | `uv run python scripts/verify_evidence.py` | Hash chain intact, every payload hash recomputed |
| Grounding and honesty | `python3 scripts/audit/verify_grounding.py` | Addendum sections 2 and 5: risks named with mitigations, every use case bound to a real dataset, every pitch-facing figure sourced |

An unsourced number on a pitch-facing surface is a critical finding equal to a fabricated benchmark.

## 4. Wave schedule

| Wave | Name | Mode | Leads | Gate |
|---|---|---|---|---|
| 0 | Foundation | Single-threaded | ARCHITECT | `docs/audit/wave0_signoff.md` |
| 1 | Parallel Core | Four concurrent workstreams | BANDIT, GOVERNANCE, HARNESS plus SENTINEL, RASHID | `docs/audit/wave1_signoff.md` |
| 2 | The Proof | BANDIT leads, AUDITOR embedded | BANDIT | `docs/audit/wave2_signoff.md` plus client checkpoint |
| 3 | Experience | Three concurrent workstreams | ATELIER, ARCHITECT plus HARNESS, GOVERNANCE plus RASHID | `docs/audit/wave3_signoff.md` |
| 4 | The Stage | DIRECTOR leads | DIRECTOR | `docs/audit/wave4_signoff.md` |
| 5 | Final Audit and Freeze | AUDITOR sole | AUDITOR | `docs/audit/final_signoff.md` plus client checkpoint, then tag `v1.0-pitch` |

## 5. Dependency graph

```
Wave 0 scaffold
   |
   +--> W1.1 BANDIT engine ---------------+
   +--> W1.2 GOVERNANCE controls ---------+--> Wave 2 proof --> W3.1 ATELIER dashboard --+
   +--> W1.3 HARNESS + SENTINEL fabric ---+                 --> W3.2 streaming + hardening +--> Wave 4 stage --> Wave 5 freeze
   +--> W1.4 RASHID Arabic layer ---------+                 --> W3.3 certificate PDF ------+
```

Hard edges. Wave 2 cannot start until the engine, the control set, the suite runners and the Arabic suites all exist, because the proof measures adaptive against exhaustive across the real suites. Wave 3 cannot start until the stopping configuration is frozen by Wave 2, because the dashboard renders confidence bounds produced by that configuration. Wave 4 cannot start until the full flow runs offline.

Soft edges. GOVERNANCE publishes the control schema as its first act in Wave 1 so BANDIT and HARNESS can code against it rather than waiting for the full control set. RASHID publishes the string catalogue key contract early for the same reason.

## 6. Acceptance criteria per wave

### Wave 0
1. Monorepo scaffolded: `engine`, `agents`, `api`, `web`, `suites`, `docs`, `scripts`.
2. FastAPI skeleton serving a health endpoint.
3. SQLite with a Postgres-ready schema covering `models`, `use_cases`, `controls`, `evaluations`, `evidence`, `certificates`, `engine_memory`.
4. React and Vite shell carrying the ATELIER design tokens, bilingual scaffolding present from the first commit.
5. Seed and reset scripts.
6. `make dev` brings up API and UI. `make test` runs the suite.
7. Schema documented in `docs/ARCHITECTURE.md`.

### Wave 1
1. Engine unit tests green, including determinism under fixed seed and a decision-parity test against exhaustive evaluation.
2. MIZAN control set encoded and mapped clause-by-clause to published UAE AI Governance Framework principles, with any MIZAN-defined control explicitly labelled as such.
3. Five government use cases with weighted mandatory and advisory controls plus confidence thresholds.
4. Model card and datasheet schemas extended with UAE governance and PDPL fields.
5. Capability suite 50 bilingual items, safety and refusal integrity 40 probes, bias 30 probes, red-team probe engine operational.
6. Deterministic mock endpoint adapter allows the full evaluation to run with no network.
7. Arabic suite items are Arabic-native, not translations, and are marked with provenance.
8. A scripted headless end-to-end evaluation of one mock model completes and writes an evidence bundle with SHA-256 hashes.

### Wave 2
1. `scripts/prove_reduction.py` runs exhaustive and adaptive evaluation over identical models and suites.
2. Query counts, wall-clock and verdict parity logged to `docs/evidence/reduction_report.md` with charts.
3. At least 80 percent reduction with identical verdicts across the model set.
4. AUDITOR reproduces the report from a clean checkout in one command.
5. Stopping thresholds and suite weights frozen and recorded.

### Wave 3
1. Registry view with Certified, Rejected, In Evaluation and Pending states.
2. Live evaluation theatre: budget visibly flowing between suite arms, confidence bounds tightening in real time, early-stop events firing with a stated reason.
3. Certificate view with every score linking down to raw evidence.
4. Cumulative national time-saved banner driven by real evaluation records.
5. Bilingual toggle with true RTL mirroring, including number and punctuation directionality.
6. Websocket streaming of evaluation traces, with an offline fallback that cannot fail.
7. Signed bilingual certificate PDF, control-by-control, evidence hashes present, print-perfect.
8. Full flow runs live and offline without intervention.
9. **The evidence tier is legible at a glance, not only on inspection.** GOVERNANCE has ruled that the certificate retains the title "MIZAN Certificate of AI Compliance" for both evidence tiers, on the reading that Compliance names the instrument rather than a statistical claim, and the budget-tier body text states plainly that the required pass rate was not demonstrated at the declared confidence. That ruling is accepted and the drafting is careful. It leaves one residual risk that belongs to the visual layer rather than to the wording: on a projected certificate a reader takes in the title and the verdict first, so a large title and a large CERTIFIED can overwhelm an honest sentence set below them, and the document would then mislead by hierarchy while every word on it remains true. The two-register rule therefore applies to the certificate's top line, not only to its control rows. The `evidence_tier` value must sit in the primary visual hierarchy beside the verdict, at a size and contrast a judge reads from the back of a room. AUDITOR tests this by reading a rendered certificate at projection distance, not by confirming the field is present in the schema.
10. Advisory controls, where the engine rationally declined to buy evidence, are visibly distinguished from mandatory controls that were evaluated. A reader must not be able to click an advisory control expecting evidence and find none.

### Wave 4
1. Registry seeded with eight historical evaluations derived from real script runs.
2. Three-minute choreography scripted and rehearsed.
3. The gasp moment implemented: a live failure on an Arabic-native safety probe with evidence one click away, followed by certification of the compliant model.
4. Backup recording captured.
5. Ten-slide deck and one-page technical brief in `docs/submission/`.

### Wave 5
1. Clean-checkout reproduction of the proof.
2. Register sweep of every string and document.
3. Evidence-linkage spot checks from certificate down to raw probe.
4. RTL visual review.
5. Three consecutive demo dry runs without failure.
6. `docs/audit/final_signoff.md` lists zero open critical findings.
7. Tag `v1.0-pitch`, export to `docs/submission/`.

## 7. Definition of done

Reproduced verbatim from charter section 6 and audited against on Wave 5. `make demo` performs the entire pitch flow, live or offline, in under three minutes, three consecutive times without failure. The reduction proof reproduces from clean checkout in one command. One model certified and one rejected, each with a signed bilingual PDF whose every score links to hashed evidence. UI and documents flawless in both languages. Submission pack complete with every claim traceable to `docs/evidence/`. Final signoff with zero open critical findings.

## 8. Audit protocol

AUDITOR is adversarial by charter and looks for the reason to reject. AUDITOR never reviews its own work and never writes build code. Each signoff file records: criteria met, findings by severity (critical, major, minor), remediation owner, and re-verification result. A wave closes only when zero critical and zero major findings remain open.

## 9. Client checkpoints

Two, and only two, hard stops for the client.

1. On Wave 2 completion: report the measured reduction figure from `docs/evidence/reduction_report.md` before opening Wave 3.
2. Before tagging `v1.0-pitch`: present the final audit summary.

All other waves proceed autonomously behind audit gates.

## 10. Subagent containment

Every dispatched specialist operates under the following standing constraints, included in each task prompt.

1. Filesystem scope limited to `~/work/mizan`. No writes elsewhere.
2. No `git push`, no remote operations, no deployment, no package publication.
3. No reading of credentials, keys, tokens or `.env` files anywhere on the machine. The system runs on deterministic mock endpoints by design.
4. No outbound network calls requiring authentication. Offline-first is a charter requirement, not a limitation.
5. No irreversible action of any kind. The only externally visible act in this engagement is a local git tag at the end, gated on the client checkpoint.
6. Each specialist writes a completion report to `docs/reports/<agent>_<wave>.md`.

Rationale: several subagents on one machine under one login are one principal wearing several names. Scope is therefore constrained at dispatch rather than assumed from persona.

## 11. Escalation

A genuine external unknown, such as a credential or a paid API, is implemented as a clean mock behind an interface, marked `# SOVEREIGN-TODO`, logged in `docs/DECISIONS.md`, and the work proceeds. No stalling.
