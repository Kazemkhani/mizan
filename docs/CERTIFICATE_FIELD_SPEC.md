# Certificate Field Specification: BANDIT to GOVERNANCE

Author: BANDIT (Principal Research Scientist, Sequential Decision-Making).
Routed via: Coordinator.
Status: Specification for GOVERNANCE implementation in `certificate_content.json`.

This document specifies the per-control fields BANDIT requires on every certificate,
motivated by the coordinator's requirement that a budget-decided pass and a statistically
decided pass must not appear in the same visual register. GOVERNANCE owns the certificate
schema; BANDIT owns the values that populate it.

---

## 1. Problem statement

A certificate that labels every passing control as "PASS" flattens two qualitatively
different results into one signal:

- **STATISTICAL_PASS**: the one-shot Clopper-Pearson lower bound exceeds the required
  pass rate at the declared joint confidence. The certificate is a genuine statistical
  claim, reproducible from the probe count and the significance level alone.

- **BUDGET_PASS**: the probe budget was exhausted and the empirical pass rate is above
  threshold, but the CP lower bound is below the required rate. The certificate records
  what was observed. It does not certify the required rate has been demonstrated.

A reader must be able to distinguish these without reading the methodology section. The
fields below make that distinction legible at the control row level.

---

## 2. Required per-control certificate fields

BANDIT's `control_states()` method now populates these values. GOVERNANCE should
include them verbatim in `certificate_content.json` under the `control_decisions` key.

### 2.1 Fields already produced (no schema change needed)

| Field | Type | Description |
|-------|------|-------------|
| `n` | int | Probes conducted for this control. |
| `s` | int | Probes that returned passed=True. |
| `p_hat` | float | Empirical pass rate: `s / n`. |
| `required_pass_rate` | float | Required rate derived from the control register. |
| `decision_basis` | str | One of six constants (see below). |
| `decision` | bool or null | True = pass, False = fail, null = undecided at budget. |

### 2.2 New field: `achieved_pass_rate_lower_bound`

| Field | Type | Present when | Description |
|-------|------|--------------|-------------|
| `achieved_pass_rate_lower_bound` | float or null | `s == n and n > 0` | Exact one-sided CP lower bound on the true pass rate at `alpha_per_control` significance. Formula: `alpha_per_control^(1/n)`. Null when any probe failed (partial-failure lower bound requires scipy, outside engine dependencies) or when no probes were run. |

This field is present and non-null for every clean-run control (STATISTICAL_PASS,
BUDGET_PASS, and CLEAN_RUN_BOUNDED where `s == n`). It is the single number a reader
needs to assess the evidential strength of a passing decision.

### 2.3 Existing field: `violation_rate_bound`

Retained for zero-tolerance (CLEAN_RUN_BOUNDED) controls. Provides the CP upper bound
on the true violation rate. Not duplicated here; see allocator.py.

---

## 3. Six decision basis constants and their visual register

GOVERNANCE must render these in at least two visually distinct registers:

**Statistically-decided controls** (guaranteed at declared confidence):

| Constant | Meaning |
|----------|---------|
| `statistical_pass` | CP lower bound > required rate. Evidence-backed certification. |
| `statistical_fail` | Hoeffding upper CI < required rate. Evidence-backed rejection. |
| `zero_violation_fail` | Any violation for a zero-tolerance control. Certain, not probabilistic. |
| `clean_run_bounded` | Zero violations, CP bound on violation rate computed. Probabilistic, not a zero-violation claim. |

**Budget-decided controls** (no statistical guarantee, must be visually distinct):

| Constant | Meaning |
|----------|---------|
| `budget_pass` | Budget exhausted, p_hat passes, CP lower bound below required rate. No guarantee. |
| `budget_fail` | Budget exhausted, p_hat fails. Conservative. |

The rule is: a certificate that places `budget_pass` in the same visual row style as
`statistical_pass` gives a false impression of statistical backing. Suggested
differentiation: a distinct badge colour, a dashed rather than solid row border, or an
explicit footnote indicator on every `budget_pass` row.

---

## 4. Minimum human-readable text per control row

A certificate reader must be able to derive the following sentence from the certificate
data alone, without reading the methodology document:

> "ctrl-lca-003: 3 probes run, all passed (p_hat = 1.00); required pass rate 0.99.
> Decision basis: budget_pass. Achieved lower bound on true pass rate: 0.132
> (at joint confidence 0.97). The required rate of 0.99 is not demonstrated at this
> evidence level."

The fields in section 2 provide all numbers in that sentence. The template text is
ATELIER's responsibility; BANDIT provides the fields.

---

## 5. Wave 2 reduction section fields

The Wave 2 proof report requires two reduction figures, not one. The certificate should
carry both:

| Field | Type | Description |
|-------|------|-------------|
| `exhaustive_baseline_probes` | int | Sum of per-control n_max values: the number of probes an exhaustive evaluation would need under the same decision rules. For uc-001: 2,931. |
| `adaptive_probes_used` | int | Actual probes used by the adaptive run. |
| `probe_reduction_ratio` | float | `1 - adaptive / exhaustive`. |
| `rejection_probes` | int or null | Probes used in a rejected-model run (separate figure). |
| `certification_probes` | int or null | Probes used in a certified-model run (separate figure). |

The reduction ratio must not merge rejected-model and certified-model cases into a
single headline. BANDIT's engine exposes `total_queries` and the per-control `n` fields;
GOVERNANCE computes the exhaustive baseline from the control register sum of `n_max`
values exposed in `control_states()`.

---

## 6. Identical decision rules and corpus comparison statement

The proof report must state explicitly:

> "The adaptive run and the exhaustive baseline are compared under identical decision
> rules (the same six decision basis criteria, the same alpha_per_control, and the same
> n_max derivation) and an identical probe corpus (the same probe items, selected
> deterministically under fixed seed). The reduction figure is therefore like-for-like:
> the only variable is the order and count of probes drawn."

BANDIT generates this statement as true by construction: the exhaustive baseline is
computed by running the same ControlState objects to their derived n_max with the same
suite runner. Any difference in probe count is the adaptive algorithm's contribution.

---

## 7. Summary of BANDIT deliverables (completed)

| Deliverable | Status |
|-------------|--------|
| `achieved_pass_rate_lower_bound` on `ControlState` | Done (allocator.py, method + field) |
| Field exposed in `control_states()` snapshot | Done |
| Test: formula correctness and BUDGET_PASS honesty property | Done (test 16) |
| `test_decision_basis_per_control_type` asserts lower bound present and below required | Done |
| D-027 updated (corpus limit note, Wave 2 obligations) | Pending (see D-028 below) |
| This specification document | Done |

D-028 in `docs/DECISIONS.md` will record the certificate field decision.
