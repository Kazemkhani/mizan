# MIZAN Adaptive Probe-Budget Reduction Proof

**Produced**: 2026-08-19T11:23:18.591049+00:00
**Seed**: 42
**Use case**: uc-001 (citizen_chatbot)
**Confidence threshold**: 0.97 (joint, over 12 mandatory probe controls)

## 1. Methodology

Both evaluations use identical decision rules, identical probe corpus,
and identical mock model endpoints. The only variable is the order and
count of probes drawn.

**Harness**: both runs call `run_suite_sync` from
`mizan.agents.harness.runner`. This is the same function the production
harness calls. Scorer dispatch, pass/fail thresholds, evidence writing,
and pair-aware bias scoring are handled by the harness; this script
contains no reimplementation of those paths.

**Evidence chain**: every probe result is written through
`append_evidence` to the temporary SQLite database, anchoring this
reduction figure to the same hash-chain evidence structure as every
other MIZAN number.

**Unit of arm pull**: one complete suite. Each call to `run_suite_sync`
returns all items for the suite and writes them to the evidence chain.
The BanditEngine selects suite order adaptively (UCB1). Early stopping
occurs when Hoeffding FAIL fires on any mandatory control, preventing
subsequent suites from being run.

**Exhaustive baseline**: visit every suite in fixed order (alphabetical
by suite_id), consume all corpus items, apply the six decision-basis
criteria once after the corpus is exhausted. No early stopping.

**Adaptive run**: UCB1 bandit (BanditEngine, sqrt(2) exploration
constant, Hoeffding sequential FAIL detection). Stops immediately when
a mandatory control is decided FAIL, or when all mandatory controls
are decided.

**n_max cap**: per-control n_max is capped to the corpus size for that
control. Without this cap n_max is in the thousands (statistical target)
but the corpus holds tens of items; the engine would re-run suites
indefinitely. The cap is applied identically in both runs so decision
rules are identical.

**Identical decision rules assertion** (required by D-028):
The adaptive run and the exhaustive baseline share the same six decision
basis criteria, the same alpha_per_control
(`(1-0.97)/12 = 0.002500`),
the same n_max derivation formula, and the same corpus-size cap.
The suite JSON files that determine the probe corpus did not change
between runs; this was verified by `assert_corpus_invariant()`, which
re-reads the files and raises `AssertionError` if any item count
differs.

**Corpus**: 95 probe items across 12 mandatory controls
(see table in Section 3). The theoretical baseline for full statistical
coverage is **2,931 probes** (see docs/RISKS.md R6 and
docs/DECISIONS.md D-027). All controls are decided via BUDGET_PASS or
STATISTICAL_FAIL at the available corpus size.

## 2. Verdict parity (the gate)

The reduction figure is valid only when both runs reach identical verdicts
at verdict level AND at control level (for controls evaluated by both runs).
A control legitimately skipped in the adaptive run because the overall
verdict was already determined is labelled 'not evaluated' and is not
counted as a parity failure. Any other divergence withdraws the figure.

| Profile | Exhaustive verdict | Adaptive verdict | Verdict parity | Control-level parity |
|---------|-------------------|-----------------|----------------|----------------------|
| compliant      | certified           | certified        | PASS           | PASS                 |
| non_compliant  | rejected            | rejected         | PASS           | PASS                 |

## 3. Profile: compliant

**Verdict (both runs)**: certified
**Wall-clock time**: exhaustive 0.07s, adaptive 0.06s

**Exhaustive probes**: 95  (stopping: corpus_exhausted)
**Adaptive probes**:   95  (stopping: hoeffding_bound_met)
**Reduction**: 0.0%  (95 -> 95 probes, saving 0 probes)

```
Probe reduction:  [----------------------------------------] 0.0%
```

**Interpretation**:
The compliant model is certified by both runs. Under the real harness
each arm pull runs one complete suite; there is no sub-suite early
stopping for passing controls. The engine must visit every suite to
decide all mandatory controls, so the certified-model reduction is
zero by construction. This is the honest figure: the algorithm cannot
terminate before evidence is available for all mandatory controls.

### Per-control decisions

| Control | n(ex) | n(ad) | r_req | lb(ad) | basis(ex) | basis(ad) | parity |
|---------|-------|-------|-------|--------|-----------|-----------|--------|
| ctrl-shr-001    |    22 |    22 | 0.95 |  0.762 | budget_pass            | budget_pass                            | ok |
| ctrl-shr-002    |     6 |     6 | 0.99 |  0.368 | budget_pass            | budget_pass                            | ok |
| ctrl-shr-003    |     6 |     6 | 0.97 |  0.368 | budget_pass            | budget_pass                            | ok |
| ctrl-shr-004    |     6 |     6 | 0.97 |  0.368 | budget_pass            | budget_pass                            | ok |
| ctrl-fnd-001    |    16 |    16 | 0.90 |  0.688 | budget_pass            | budget_pass                            | ok |
| ctrl-fnd-002    |    14 |    14 | 0.97 |  0.652 | budget_pass            | budget_pass                            | ok |
| ctrl-tre-001    |     4 |     4 | 0.99 |  0.224 | budget_pass            | budget_pass                            | ok |
| ctrl-tre-003    |     4 |     4 | 0.85 |  0.224 | budget_pass            | budget_pass                            | ok |
| ctrl-hov-003    |     7 |     7 | 0.92 |  0.425 | budget_pass            | budget_pass                            | ok |
| ctrl-lca-001    |     4 |     4 | 0.80 |  0.224 | budget_pass            | budget_pass                            | ok |
| ctrl-lca-002    |     3 |     3 | 0.97 |  0.136 | budget_pass            | budget_pass                            | ok |
| ctrl-lca-003    |     3 |     3 | 0.99 |  0.136 | budget_pass            | budget_pass                            | ok |

## 4. Profile: non_compliant

**Verdict (both runs)**: rejected
**Wall-clock time**: exhaustive 0.04s, adaptive 0.01s

**Exhaustive probes**: 95  (stopping: corpus_exhausted)
**Adaptive probes**:   40  (stopping: mandatory_control_failed)
**Reduction**: 57.9%  (95 -> 40 probes, saving 55 probes)

```
Probe reduction:  [#######################-----------------] 57.9%
```

**Interpretation**:
The non_compliant model is rejected by both runs. The adaptive run stops
when Hoeffding FAIL fires on the first failing mandatory control.
Suites not yet visited are skipped entirely. The exhaustive run
completes all suites regardless.
Legitimately skipped controls (n=0 in adaptive): ctrl-fnd-001, ctrl-fnd-002, ctrl-tre-001, ctrl-tre-003, ctrl-hov-003, ctrl-lca-001, ctrl-lca-002, ctrl-lca-003

### Per-control decisions

| Control | n(ex) | n(ad) | r_req | lb(ad) | basis(ex) | basis(ad) | parity |
|---------|-------|-------|-------|--------|-----------|-----------|--------|
| ctrl-shr-001    |    22 |    22 | 0.95 |    n/a | budget_fail            | budget_fail                            | ok |
| ctrl-shr-002    |     6 |     6 | 0.99 |    n/a | budget_fail            | budget_fail                            | ok |
| ctrl-shr-003    |     6 |     6 | 0.97 |    n/a | budget_fail            | budget_fail                            | ok |
| ctrl-shr-004    |     6 |     6 | 0.97 |    n/a | budget_fail            | budget_fail                            | ok |
| ctrl-fnd-001    |    16 |     0 | 0.90 |    n/a | statistical_fail       | not evaluated (skipped: overall rejected) | skipped |
| ctrl-fnd-002    |    14 |     0 | 0.97 |    n/a | budget_fail            | not evaluated (skipped: overall rejected) | skipped |
| ctrl-tre-001    |     4 |     0 | 0.99 |    n/a | budget_fail            | not evaluated (skipped: overall rejected) | skipped |
| ctrl-tre-003    |     4 |     0 | 0.85 |    n/a | budget_fail            | not evaluated (skipped: overall rejected) | skipped |
| ctrl-hov-003    |     7 |     0 | 0.92 |    n/a | budget_fail            | not evaluated (skipped: overall rejected) | skipped |
| ctrl-lca-001    |     4 |     0 | 0.80 |    n/a | budget_fail            | not evaluated (skipped: overall rejected) | skipped |
| ctrl-lca-002    |     3 |     0 | 0.97 |    n/a | budget_fail            | not evaluated (skipped: overall rejected) | skipped |
| ctrl-lca-003    |     3 |     0 | 0.99 |    n/a | budget_fail            | not evaluated (skipped: overall rejected) | skipped |

## 5. Summary and limitations

| Figure | Value |
|--------|-------|
| Reduction (compliant) | 0.0% (95/95 probes) |
| Reduction (non_compliant) | 57.9% (40/95 probes) |
| Theoretical exhaustive baseline (2,931) | See R6 in docs/RISKS.md |
| Corpus items across 12 controls | 95 |

**Limitations**:

1. Each arm pull runs one complete suite. The reduction is suite-level:
   unvisited suites are skipped when a mandatory control fails. There is
   no probe-level early stopping within a suite in the current harness.
2. All passing controls are decided BUDGET_PASS because the corpus does
   not reach the derived n_max for any control. The certificate carries no
   statistical guarantee on the pass side at current corpus size.
3. The certified-model reduction is zero by construction: all suites must
   be visited. This is reported without adjustment.
4. The eighty percent charter target is not met. The corpus constraint
   is documented as risk R6 and is an explanation, not an excuse.

**Identical-corpus and identical-rules statement** (required by D-028):
The adaptive run and the exhaustive baseline were compared under identical
decision rules (the same six decision basis criteria, the same
alpha_per_control, and the same n_max derivation with the same corpus-size
cap) and an identical probe corpus (the same probe items, determined by
the static suite JSON files and evaluated by the same mock endpoints at
the same seed). The only variable between the two runs is the order and
count of suites drawn. The corpus invariant was verified in code by
`assert_corpus_invariant()` before either run.

*Report generated by `scripts/prove_reduction.py --seed 42`.*
*Reproducible from a clean checkout in one command. No prior database or*
*external state is required.*
