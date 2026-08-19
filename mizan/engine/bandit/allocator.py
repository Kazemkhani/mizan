"""UCB1 bandit allocator with Hoeffding sequential stopping.

REWARD FORMULATION
==================
Arms are test suites. The reward at each pull is the *information gain
toward the certification decision*, measured as reduction in Shannon
entropy over the mandatory-control pass-rate estimates.

For each mandatory control k, MIZAN maintains a Bernoulli estimate
p_hat_k = (passing probes for k) / (total probes for k), initialised at
0.5 (maximum uncertainty). The decision entropy for one control is:

    H(p) = -p * log2(p) - (1-p) * log2(1-p)        [bits, with H(0)=H(1)=0]

After a suite arm is pulled and its probes are processed, the information
gain is:

    IG = sum_{k in mandatory_controls_of_suite} [H(p_hat_k_before) - H(p_hat_k_after)]

This is normalised into [0, 1] by dividing by K_mandatory (the total
number of mandatory controls for the evaluation), because each control
contributes at most H(0.5) - H(1.0) = 1.0 bit:

    reward = IG / K_mandatory

This reward has a natural interpretation: what fraction of the total
certification uncertainty did this arm pull resolve?

NORMALISATION COST
==================
Dividing by K_mandatory rather than by K_suite (the number of mandatory
controls covered by the pulled suite) means a suite covering few controls
earns proportionally less reward per pull than one covering many. This is
correct: a suite that only covers two controls resolves less total
uncertainty than one covering five, and UCB1 should allocate budget
accordingly. The trade-off is that rewards become small when K_mandatory
is large (e.g., 13 for citizen_chatbot), which shrinks the UCB exploration
bonus. The exploration constant c is chosen to compensate; the default
c = sqrt(2) (Auer et al. 2002) remains appropriate.

STOPPING RULE: UNION-BOUND-CORRECTED HOEFFDING
===============================================
The naive approach, applying Hoeffding's inequality at a fixed n and
stopping as soon as the bound separates from the threshold, is invalid
under data-dependent stopping: sequential peeking inflates the error
rate, because the fixed-sample-size bound holds at a predetermined n,
not at an arbitrary stopping time.

MIZAN uses a union-bound correction over a finite grid of at most n_max
possible stopping times. For each mandatory control k:

    delta_total = 1 - confidence_threshold       (total error budget)
    delta_per_control = delta_total / K           (Bonferroni over K controls)
    delta_corrected = delta_per_control / n_max   (Bonferroni over n_max peeks)

At n probes, the half-width of the Hoeffding confidence interval is:

    eps(n) = sqrt( ln(2 / delta_corrected) / (2 * n) )

The control is decided (see current_decision_basis() for the full routing):
  - STATISTICAL_FAIL      if p_hat_k + eps(n_k) < required_pass_rate_k
  - STATISTICAL_PASS      if n_k >= n_max_k and s_k == n_k and p_lower > required_pass_rate_k
  - ZERO_VIOLATION_FAIL   if required_pass_rate_k == 1.0 and any violation observed
  - CLEAN_RUN_BOUNDED     if required_pass_rate_k == 1.0, n_k >= n_max, 0 violations
                            (bound: p_upper = 1 - delta_corrected^(1/n_k))
  - BUDGET_PASS           if n_k >= n_max and p_hat_k >= required_pass_rate_k  [no guarantee]
  - BUDGET_FAIL           if n_k >= n_max and p_hat_k < required_pass_rate_k   [no guarantee]

ERROR GUARANTEE (PER DECISION CLASS)
======================================
The guarantee is not uniform: it depends on which criterion decided each control.

STATISTICAL_FAIL and STATISTICAL_PASS (Hoeffding-decided controls):
    By Hoeffding's inequality, at any fixed n:
        Pr(wrong decision at this n) <= 2 * exp(-2 * n * eps(n)^2) = delta_corrected
    Union bound over n_max peeks and K controls:
        Pr(any Hoeffding-decided control wrongly decided) <= K * n_max * delta_corrected
                                                          = 1 - confidence_threshold
    Guarantee: with probability >= confidence_threshold, every Hoeffding-decided
    mandatory control is correctly classified. This is exact; no asymptotic
    qualification applies.

ZERO_VIOLATION_FAIL (zero-tolerance, any violation observed):
    Certain, not probabilistic. Any observed violation for a control with
    required_pass_rate = 1.0 establishes that the true violation rate is >= 1/n > 0,
    refuting the zero-tolerance requirement directly. No confidence budget is consumed.

CLEAN_RUN_BOUNDED (zero-tolerance, 0 violations, budget exhausted):
    A real statistical statement using the same delta_corrected budget. With 0
    violations in n probes, the one-sided Clopper-Pearson upper bound on the true
    violation rate p is:
        p_upper = 1 - delta_corrected^(1/n)
    With probability >= confidence_threshold, the true violation rate is below p_upper.
    The certificate records n and p_upper, not "zero violation rate": the claim is
    "no violation observed in n adversarial probes; rate bounded below p_upper."

BUDGET_PASS (non-zero-tolerance, budget exhausted, p_hat >= required_pass_rate):
    No statistical guarantee. The budget was exhausted before the CP lower bound
    could be asserted. This arises when the test cap (n_max_per_control in
    engine_config) is tighter than the statistically derived n_max, or when a
    model fails to produce a clean run. The certificate must label these decisions
    "budget-limited: no statistical guarantee." Wave 2 reduction: the pass-side
    reduction metric distinguishes STATISTICAL_PASS decisions (full budget reached,
    CP lower bound asserted) from BUDGET_PASS decisions (cap hit, no guarantee).
    At the full derived n_max, every passing model is decided STATISTICAL_PASS;
    BUDGET_PASS is only an artefact of a cap or of a model that fails some probes.

BUDGET_FAIL (non-zero-tolerance, budget exhausted, p_hat < required_pass_rate):
    No statistical guarantee, but rejection is the conservative outcome and less
    likely to cause harm than erroneous certification.

CHOICE OF UNION BOUND OVER ANYTIME-VALID BOUNDS
================================================
An anytime-valid alternative (Howard et al. 2021, "Time-uniform,
nonparametric, nonasymptotic confidence sequences") would apply a
log-correction factor: eps(n) proportional to sqrt(log(log(n)) / n),
avoiding the need to specify n_max in advance. MIZAN uses the union-bound
approach because:
1. The demo operates with a fixed probe budget (n_max), making a finite
   grid natural rather than an approximation.
2. The union-bound guarantee is exact and stated without asymptotic
   qualifications, which is required for a government certification system.
3. The mechanism is explainable in one slide: "we reserved error budget for
   at most n_max checks, so the total error is bounded."
The cost is that n_max must be set in advance; the engine stops via
budget_exhausted if n_max is insufficient to separate the bound.

UCB1 ARM SELECTION
==================
UCB1_i = mean_reward_i + c * sqrt(ln(t) / n_i)

where t is total pulls so far, n_i is pulls for arm i, and c = sqrt(2)
(Auer et al. 2002 theorem 1). Unvisited arms are pulled first, in the
order provided by the MCSS warm-start. Arms whose mandatory controls are
all decided are skipped (the arm contributes no further information).

References:
    Hoeffding, W. (1963). Probability inequalities for sums of bounded
    random variables. J. Amer. Statist. Assoc. 58, pp. 13-30.

    Auer, P., Cesa-Bianchi, N., and Fischer, P. (2002). Finite-time
    analysis of the multiarmed bandit problem. Machine Learning 47,
    pp. 235-256.

    Howard, S.R., Ramdas, A., McAuliffe, J., and Sekhon, J. (2021).
    Time-uniform, nonparametric, nonasymptotic confidence sequences.
    Ann. Statist. 49(2), pp. 1055-1080.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from mizan.api.schemas import ArmPull


# ---------------------------------------------------------------------------
# Decision basis constants (strings for direct serialisability).
#
# Each mandatory control is decided by exactly one of these criteria.
# PASS bases: STATISTICAL_PASS, CLEAN_RUN_BOUNDED, BUDGET_PASS.
# FAIL bases: STATISTICAL_FAIL, ZERO_VIOLATION_FAIL, BUDGET_FAIL.
#
# Certificate consumers must inspect decision_basis per control: BUDGET_PASS
# in particular carries no statistical guarantee and must be labelled as such.
# ---------------------------------------------------------------------------

STATISTICAL_PASS    = "statistical_pass"    # exact CP lower bound > required_pass_rate (one-shot at budget)
STATISTICAL_FAIL    = "statistical_fail"    # Hoeffding upper CI < required_pass_rate
ZERO_VIOLATION_FAIL = "zero_violation_fail" # zero-tolerance: any violation observed
CLEAN_RUN_BOUNDED   = "clean_run_bounded"   # zero-tolerance: 0 violations, budget done, rate bounded
BUDGET_PASS         = "budget_pass"         # budget exhausted, p_hat passes, no guarantee
BUDGET_FAIL         = "budget_fail"         # budget exhausted, p_hat fails, no guarantee

_PASS_BASES: frozenset[str] = frozenset({STATISTICAL_PASS, CLEAN_RUN_BOUNDED, BUDGET_PASS})
_FAIL_BASES: frozenset[str] = frozenset({STATISTICAL_FAIL, ZERO_VIOLATION_FAIL, BUDGET_FAIL})


# ---------------------------------------------------------------------------
# Default engine configuration values.
# These are applied when the caller does not override them in engine_config.
# ---------------------------------------------------------------------------

DEFAULT_EXPLORATION_CONSTANT: float = math.sqrt(2)  # Auer et al. 2002
DEFAULT_TOTAL_BUDGET: int = 10000     # hard cap on total queries; raised to exceed derived budgets

# Fallback n_max for zero-tolerance controls (required_pass_rate == 1.0).
# These controls use the CLEAN_RUN_BOUNDED path rather than STATISTICAL_PASS.
# NOTE: currently unexercised. GOVERNANCE Wave 1 converted all zero-tolerance
# probe controls to attestation evidence type (evaluated outside the bandit).
# This fallback exists for correctness when a genuine zero-tolerance probe
# control appears in future.
_ZT_N_MAX_FALLBACK: int = 100


def _derive_required_pass_rate(
    pass_threshold: float,
    threshold_direction: str | None = None,
) -> float:
    """Derive the required Bernoulli pass rate from GOVERNANCE schema fields.

    Primary path (GOVERNANCE schema >= Wave 1, threshold_direction provided):
        "at_least" -> required_pass_rate = pass_threshold
                      (exception: scale controls with pass_threshold > 1.0 default to 0.8)
        "at_most"  -> required_pass_rate = 1.0 - pass_threshold

    Fallback path (threshold_direction absent, e.g., test fixtures):
        Infers polarity from the numeric value of pass_threshold.
        WARNING (D-022): silently wrong for any control with a legitimate
        required rate in [0.0, 0.5) that is an "at_least" control.
        GOVERNANCE should carry the field explicitly; the engine should not guess.
    """
    if threshold_direction == "at_least":
        if pass_threshold > 1.0:
            return 0.8  # non-Bernoulli scale fallback
        return pass_threshold
    if threshold_direction == "at_most":
        return 1.0 - pass_threshold
    # Legacy fallback: infer from threshold value (D-022 latent major).
    if pass_threshold > 1.0:
        return 0.8
    if pass_threshold >= 0.5:
        return pass_threshold
    return 1.0 - pass_threshold


def _min_probes_for_statistical_pass(
    required_pass_rate: float,
    alpha_per_control: float,
) -> int:
    """Exact minimum n for a one-shot Clopper-Pearson lower bound to certify required_pass_rate.

    With n perfect probes (all pass), the one-sided Clopper-Pearson lower bound
    on the true pass rate at significance alpha_per_control is:

        p_lower = alpha_per_control^(1/n)

    This exceeds required_pass_rate when:

        n >= ln(alpha_per_control) / ln(required_pass_rate)

    Both logarithms are negative; their ratio is positive.

    This is the correct exhaustive-baseline budget for Wave 2: compare the
    adaptive evaluation against this n (derived from control thresholds and the
    confidence level) rather than an arbitrary cap. That way the reduction figure
    means something: MIZAN reached the same verdict as a statistically complete
    evaluation at a fraction of its budget.

    For zero-tolerance controls (required_pass_rate >= 1.0):
        ln(1.0) = 0; the formula has no solution. Returns _ZT_N_MAX_FALLBACK.
        These controls use the CLEAN_RUN_BOUNDED path.

    For non-Bernoulli scale controls (required_pass_rate derived as 0.8):
        The formula applies normally.
    """
    if required_pass_rate >= 1.0:
        return _ZT_N_MAX_FALLBACK
    return math.ceil(math.log(alpha_per_control) / math.log(required_pass_rate))


# ---------------------------------------------------------------------------
# Control state tracker
# ---------------------------------------------------------------------------

@dataclass
class ControlState:
    """Tracks the empirical pass-rate estimate for one compliance control.

    All attributes are mutable; the engine updates n and s in-place as probes
    arrive.
    """

    control_id: str
    suite_id: str
    is_mandatory: bool
    required_pass_rate: float  # derived from pass_threshold + threshold_direction

    # Per-control budget parameters set by BanditEngine at construction.
    # n_max: minimum probes for STATISTICAL_PASS (from _min_probes_for_statistical_pass).
    # alpha_per_control: (1 - confidence_threshold) / K_mandatory, for CP lower bound.
    # delta_corrected: alpha_per_control / n_max, for Hoeffding sequential FAIL detection.
    n_max: int = field(default=_ZT_N_MAX_FALLBACK)
    alpha_per_control: float = field(default=0.05)
    delta_corrected: float = field(default=0.001)

    n: int = field(default=0)  # total probes seen
    s: int = field(default=0)  # probes that returned passed=True

    # ---------------------------------------------------------------------------
    # Entropy computations
    # ---------------------------------------------------------------------------

    @property
    def p_hat(self) -> float:
        """Empirical pass rate. Returns 0.5 before any probes (maximum uncertainty)."""
        return self.s / self.n if self.n > 0 else 0.5

    @staticmethod
    def binary_entropy(p: float) -> float:
        """Shannon binary entropy in bits. H(0) = H(1) = 0 by convention."""
        if p <= 0.0 or p >= 1.0:
            return 0.0
        return -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))

    def entropy_before(self) -> float:
        """Decision entropy before the current probe update."""
        return self.binary_entropy(self.p_hat)

    def entropy_after(self, n_new: int, s_new: int) -> float:
        """Decision entropy after absorbing n_new probes of which s_new passed."""
        if self.n + n_new == 0:
            return 1.0  # still maximum uncertainty
        p_new = (self.s + s_new) / (self.n + n_new)
        return self.binary_entropy(p_new)

    def information_gain(self, n_new: int, s_new: int) -> float:
        """Entropy reduction from absorbing n_new probes. Clamped to [0, 1]."""
        return max(0.0, self.entropy_before() - self.entropy_after(n_new, s_new))

    # ---------------------------------------------------------------------------
    # Zero-tolerance helpers
    # ---------------------------------------------------------------------------

    @property
    def is_zero_tolerance(self) -> bool:
        """True when the control requires a zero observed violation rate.

        A control is zero-tolerance when required_pass_rate == 1.0. The
        Hoeffding PASS condition (p_hat - eps > 1.0) is structurally
        impossible for this class because p_hat <= 1.0 and eps > 0. These
        controls use the clean-run-bounded decision path instead.
        """
        return self.required_pass_rate >= 1.0

    def violation_rate_upper_bound(self) -> float:
        """Exact one-sided Clopper-Pearson upper bound on the true violation rate.

        With 0 violations (self.s == self.n) in n independent Bernoulli probes,
        the (1 - delta_corrected) one-sided confidence upper bound on the true
        violation probability p satisfies:

            (1 - p)^n = delta_corrected
            => p_upper = 1 - delta_corrected^(1/n)

        Uses self.delta_corrected (pre-allocated per-control budget). The bound
        tightens monotonically as n increases. The rule-of-three approximation
        (-ln(delta_corrected)/n) converges to this for small delta_corrected;
        the exact form is used here.

        Returns 1.0 when n == 0 (no information).
        Only meaningful when no violations have been observed (self.s == self.n).
        """
        if self.n == 0:
            return 1.0
        return 1.0 - (self.delta_corrected ** (1.0 / self.n))

    def achieved_pass_rate_lower_bound(self) -> float | None:
        """Exact one-sided Clopper-Pearson lower bound on the true pass rate.

        For a clean run (s == n, all probes passing), the one-shot CP lower
        bound at significance alpha_per_control is:

            p_lower = alpha_per_control^(1/n)

        This is the same formula used by STATISTICAL_PASS. The difference is
        whether it exceeds required_pass_rate:

            STATISTICAL_PASS   : p_lower > required_pass_rate  (bound is certified)
            BUDGET_PASS        : p_lower <= required_pass_rate (bound is honest)

        Both cases are reported here so a certificate reader can see exactly
        what statistical strength each decision carries, regardless of whether
        the control was statistically decided or budget-decided.

        For partial failures (s < n): the exact CP lower bound requires the
        incomplete beta function (scipy). Since scipy is outside the engine's
        declared dependencies, this returns None in the partial-failure case.
        The value is not practically needed there because a partial-failure
        control is BUDGET_FAIL or STATISTICAL_FAIL (a reader already knows the
        decision was adverse).

        Returns None when n == 0 or when s < n.
        Returns 0.0 for non-mandatory controls (alpha_per_control is not
        assigned a meaningful value by the engine).
        """
        if self.n == 0 or self.s < self.n:
            return None
        return self.alpha_per_control ** (1.0 / self.n)

    # ---------------------------------------------------------------------------
    # Hoeffding stopping (non-zero-tolerance controls only)
    # ---------------------------------------------------------------------------

    def hoeffding_half_width(self) -> float:
        """Hoeffding confidence interval half-width at current sample size.

        eps(n) = sqrt( ln(2 / delta_corrected) / (2 * n) )

        Uses self.delta_corrected (per-control union-bound budget for FAIL detection).
        Returns 1.0 when no probes have been seen (interval spans [0,1]).
        """
        if self.n == 0:
            return 1.0
        return math.sqrt(math.log(2.0 / self.delta_corrected) / (2.0 * self.n))

    # ---------------------------------------------------------------------------
    # Decision routing
    # ---------------------------------------------------------------------------

    def current_decision_basis(self) -> str | None:
        """Return the decision basis for this control, or None if undecided.

        Decision routing by control class:

        Zero-tolerance controls (required_pass_rate == 1.0):
            Any violation observed         -> ZERO_VIOLATION_FAIL (certain, immediate)
            Budget exhausted, 0 violations -> CLEAN_RUN_BOUNDED (Clopper-Pearson bound)
            Otherwise                      -> undecided (None)
            NOTE: currently unexercised in production; GOVERNANCE Wave 1 converted all
            zero-tolerance probe controls to attestation evidence type.

        Non-zero-tolerance controls:
            Hoeffding upper CI < required     -> STATISTICAL_FAIL (guaranteed by union bound)
            All probes pass at self.n_max     -> STATISTICAL_PASS (exact CP lower bound)
            Budget exhausted, p_hat passes    -> BUDGET_PASS (no statistical guarantee)
            Budget exhausted, p_hat fails     -> BUDGET_FAIL (no guarantee)
            Otherwise                         -> undecided (None)

        STATISTICAL_PASS uses the exact one-shot Clopper-Pearson lower bound:
            p_lower = alpha_per_control^(1/n) > required_pass_rate
        This fires only when all n probes pass (s == n) and n >= n_max. The
        n_max is derived from the coordinator's formula so that this condition
        is exactly satisfiable at the exhaustive-baseline budget.

        Certificate consumers must check decision_basis per control.
        BUDGET_PASS carries no statistical guarantee and must be labelled as such.
        """
        if self.n == 0:
            return None

        if self.is_zero_tolerance:
            if self.s < self.n:
                return ZERO_VIOLATION_FAIL
            if self.n >= self.n_max:
                return CLEAN_RUN_BOUNDED
            return None

        # Hoeffding sequential FAIL detection (uses union-bound delta_corrected).
        eps = self.hoeffding_half_width()
        if (self.p_hat + eps) < self.required_pass_rate:
            return STATISTICAL_FAIL

        # Exact CP lower bound PASS (one-shot at budget; no sequential correction needed
        # because PASS is only checked when the full budget is consumed).
        if self.n >= self.n_max and self.s == self.n:
            p_lower = self.alpha_per_control ** (1.0 / self.n)
            if p_lower > self.required_pass_rate:
                return STATISTICAL_PASS

        if self.n >= self.n_max:
            if self.p_hat >= self.required_pass_rate:
                return BUDGET_PASS
            return BUDGET_FAIL

        return None

    def is_decided(self) -> bool:
        """True when the control has been decided by any criterion."""
        return self.current_decision_basis() is not None

    def decision(self) -> bool | None:
        """Return True for PASS, False for FAIL, None if undecided.

        PASS covers: STATISTICAL_PASS, CLEAN_RUN_BOUNDED, BUDGET_PASS.
        FAIL covers: STATISTICAL_FAIL, ZERO_VIOLATION_FAIL, BUDGET_FAIL.

        Callers building certificates must also call current_decision_basis()
        to present honest per-control guarantees. BUDGET_PASS in particular
        carries no statistical guarantee and must be labelled explicitly.
        """
        basis = self.current_decision_basis()
        if basis in _PASS_BASES:
            return True
        if basis in _FAIL_BASES:
            return False
        return None


# ---------------------------------------------------------------------------
# Arm state tracker
# ---------------------------------------------------------------------------

@dataclass
class ArmState:
    """Tracks UCB1 state for one test suite arm."""

    suite_id: str
    arm_index: int

    pulls: int = field(default=0)
    total_reward: float = field(default=0.0)
    # Cumulative reward from MCSS historical memory; used for warm-start.
    mcss_mean_reward: float = field(default=0.0)

    @property
    def mean_reward(self) -> float:
        """Empirical mean reward across all pulls of this arm."""
        return self.total_reward / self.pulls if self.pulls > 0 else 0.0

    def ucb_value(self, t: int, exploration_constant: float) -> float:
        """UCB1 index (Auer et al. 2002).

        UCB1_i = mean_reward_i + c * sqrt(ln(t) / n_i)

        Returns infinity when the arm has not been pulled, ensuring every
        arm is explored at least once before UCB1 takes effect.
        """
        if self.pulls == 0:
            return float("inf")
        return self.mean_reward + exploration_constant * math.sqrt(
            math.log(t) / self.pulls
        )

    def to_posterior_snapshot(self) -> dict:
        """Serialisable snapshot for ArmPull.posterior_state."""
        return {
            "pulls": self.pulls,
            "total_reward": round(self.total_reward, 6),
            "mean_reward": round(self.mean_reward, 6),
        }


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class BanditEngine:
    """UCB1 bandit engine for adaptive compliance evaluation.

    Inputs:
        evaluation_id:        UUID of the evaluations row being updated.
        use_case_class:       Use-case class key (matches engine_memory).
        confidence_threshold: From the use_cases row (e.g., 0.97).
        controls:             List of control dicts, each with:
                                control_id, suite_id, is_mandatory,
                                pass_threshold (float).
        engine_config:        Dict with optional keys:
                                random_seed (int, required for determinism)
                                exploration_constant (float, default sqrt(2))
                                n_max_per_control (int, optional hard cap applied to the
                                    per-control derived budget; does not replace the
                                    statistical derivation, only caps it for tests)
                                total_budget (int, default: max of sum of per-control
                                    n_max values and DEFAULT_TOTAL_BUDGET)
        mcss_ordering:        Optional list of suite_ids in MCSS priority order.
                              Unvisited arms are pulled in this order.

    Determinism contract:
        Under a fixed random_seed, the arm-pull sequence (arm indices and
        rewards) is byte-for-byte identical across multiple runs on any
        machine. The seed is consumed exclusively through self._rng, a
        numpy.random.Generator. No other source of randomness is used.
    """

    def __init__(
        self,
        evaluation_id: str,
        use_case_class: str,
        confidence_threshold: float,
        controls: list[dict],
        engine_config: dict,
        mcss_ordering: list[str] | None = None,
    ) -> None:
        self._evaluation_id = evaluation_id
        self._use_case_class = use_case_class
        self._confidence_threshold = confidence_threshold

        # Seed every source of randomness through a single Generator.
        seed = int(engine_config.get("random_seed", 0))
        self._rng: np.random.Generator = np.random.default_rng(seed)

        # Hyperparameters from engine_config.
        self._exploration_constant: float = float(
            engine_config.get("exploration_constant", DEFAULT_EXPLORATION_CONSTANT)
        )
        # n_max_per_control from config is treated as a hard cap on the derived
        # per-control budget. It does NOT replace the derivation; it prevents the
        # engine from being forced to run far beyond any reasonable budget in tests
        # that use small fixtures. Omit from config to use the full derived budget.
        _n_max_cap: int | None = (
            int(engine_config["n_max_per_control"])
            if "n_max_per_control" in engine_config
            else None
        )

        # Build control state map.
        self._controls: list[ControlState] = []
        self._control_map: dict[str, ControlState] = {}
        self._controls_by_suite: dict[str, list[ControlState]] = {}
        self._mandatory_controls: list[ControlState] = []

        for c in controls:
            ctrl = ControlState(
                control_id=c["control_id"],
                suite_id=c["suite_id"],
                is_mandatory=bool(c["is_mandatory"]),
                required_pass_rate=_derive_required_pass_rate(
                    float(c["pass_threshold"]),
                    threshold_direction=c.get("threshold_direction"),
                ),
            )
            self._controls.append(ctrl)
            self._control_map[ctrl.control_id] = ctrl
            self._controls_by_suite.setdefault(ctrl.suite_id, []).append(ctrl)
            if ctrl.is_mandatory:
                self._mandatory_controls.append(ctrl)

        # Derive per-control statistical budget parameters.
        # alpha_per_control is the per-control error budget (Bonferroni over K).
        k = max(len(self._mandatory_controls), 1)
        alpha_per_control: float = (1.0 - confidence_threshold) / k

        for ctrl in self._mandatory_controls:
            # n_max: minimum probes for the CP lower bound to fire (one-shot at budget).
            n_max_derived = _min_probes_for_statistical_pass(
                ctrl.required_pass_rate, alpha_per_control
            )
            # Apply the test cap if provided (never increases the budget).
            if _n_max_cap is not None:
                n_max_derived = min(n_max_derived, _n_max_cap)
            ctrl.n_max = n_max_derived
            ctrl.alpha_per_control = alpha_per_control
            # delta_corrected for sequential Hoeffding FAIL: Bonferroni over n_max peeks.
            ctrl.delta_corrected = max(alpha_per_control / ctrl.n_max, 1e-15)

        # Total probe budget: sum of mandatory per-control budgets, or config override.
        derived_total = sum(c.n_max for c in self._mandatory_controls) if self._mandatory_controls else DEFAULT_TOTAL_BUDGET
        self._total_budget: int = int(
            engine_config.get("total_budget", max(derived_total, DEFAULT_TOTAL_BUDGET))
        )

        # Build arm list (one arm per unique suite).
        suite_ids_ordered = list(dict.fromkeys(c["suite_id"] for c in controls))
        # Apply MCSS ordering if provided: put known suites in MCSS order first,
        # then append any remaining suites not in the MCSS ordering.
        if mcss_ordering:
            ordered: list[str] = []
            for s in mcss_ordering:
                if s in suite_ids_ordered and s not in ordered:
                    ordered.append(s)
            for s in suite_ids_ordered:
                if s not in ordered:
                    ordered.append(s)
            suite_ids_ordered = ordered

        self._arms: list[ArmState] = []
        self._suite_to_arm_index: dict[str, int] = {}
        for idx, sid in enumerate(suite_ids_ordered):
            arm = ArmState(suite_id=sid, arm_index=idx)
            self._arms.append(arm)
            self._suite_to_arm_index[sid] = idx

        # MCSS priority list: indices of arms in warm-start order.
        self._mcss_arm_order: list[int] = list(range(len(self._arms)))

        # Step and query counters.
        self._step: int = 0
        self._total_queries: int = 0

    # ---------------------------------------------------------------------------
    # Stopping helpers
    # ---------------------------------------------------------------------------

    def _is_mandatory_control_decided(self, ctrl: ControlState) -> bool:
        return ctrl.is_decided()

    def _all_mandatory_decided(self) -> bool:
        return all(self._is_mandatory_control_decided(c) for c in self._mandatory_controls)

    def _any_mandatory_failed(self) -> bool:
        for ctrl in self._mandatory_controls:
            basis = ctrl.current_decision_basis()
            if basis in _FAIL_BASES:
                return True
        return False

    def check_stopping(self) -> tuple[bool, str | None]:
        """Return (should_stop, stopping_reason) based on current control states.

        Called before each arm pull. Returns immediately on the first met
        criterion. Priority order: fail detection > all-decided > budget.
        """
        if self._any_mandatory_failed():
            return True, "mandatory_control_failed"
        if self._all_mandatory_decided():
            return True, "hoeffding_bound_met"
        if self._total_queries >= self._total_budget:
            return True, "budget_exhausted"
        return False, None

    # ---------------------------------------------------------------------------
    # Verdict
    # ---------------------------------------------------------------------------

    def final_verdict(self) -> str:
        """Compute the certification verdict from current control states.

        Returns 'certified' only when every mandatory control passed.
        A control that is undecided at budget exhaustion is evaluated on
        its empirical pass rate versus required_pass_rate.
        """
        for ctrl in self._mandatory_controls:
            decision = ctrl.decision()
            if decision is False:
                return "rejected"
            if decision is None and ctrl.p_hat < ctrl.required_pass_rate:
                # Budget-exhausted, undecided, but empirically failing.
                return "rejected"
        return "certified"

    # ---------------------------------------------------------------------------
    # Arm selection
    # ---------------------------------------------------------------------------

    def _arm_has_undecided_mandatory_controls(self, arm: ArmState) -> bool:
        """True when the arm covers at least one undecided mandatory control."""
        for ctrl in self._controls_by_suite.get(arm.suite_id, []):
            if ctrl.is_mandatory and not self._is_mandatory_control_decided(ctrl):
                return True
        return False

    def select_arm(self) -> int:
        """Select the next arm to pull.

        Phase 1 (warm-start): while any arm has not been pulled, select the
        first unvisited arm in MCSS priority order. The selection is
        deterministic (MCSS ordering is fixed at init time); no RNG is used.

        Phase 2 (UCB1): once all arms have been pulled at least once, select
        the arm with the highest UCB1 index. Ties are broken uniformly at
        random via self._rng (deterministic under fixed seed).

        Arms with all mandatory controls already decided are skipped in both
        phases.
        """
        available = [
            i for i, arm in enumerate(self._arms)
            if self._arm_has_undecided_mandatory_controls(arm)
        ]
        if not available:
            # All mandatory controls decided; fallback (should not normally be reached
            # because check_stopping fires first).
            return 0

        # Phase 1: MCSS warm-start. Pull unvisited arms in MCSS order.
        unvisited_in_order = [
            i for i in self._mcss_arm_order
            if i in available and self._arms[i].pulls == 0
        ]
        if unvisited_in_order:
            return unvisited_in_order[0]

        # Phase 2: UCB1 over visited available arms.
        t = self._step + 1
        ucb_scores = [
            self._arms[i].ucb_value(t, self._exploration_constant)
            for i in available
        ]
        best_score = max(ucb_scores)
        best_indices = [
            available[j] for j, score in enumerate(ucb_scores) if score == best_score
        ]
        if len(best_indices) == 1:
            return best_indices[0]
        # Tie-break with the seeded RNG.
        return int(self._rng.choice(best_indices))

    # ---------------------------------------------------------------------------
    # Arm pull
    # ---------------------------------------------------------------------------

    def pull(self, arm_index: int, probe_results: list[dict]) -> ArmPull:
        """Process probe results for one arm pull, update state, return ArmPull.

        Args:
            arm_index:     Index into self._arms.
            probe_results: List of probe result dicts, each with:
                             control_id (str), probe_id (str), passed (bool),
                             score (float).

        Returns:
            ArmPull schema object for streaming and persistence.
        """
        arm = self._arms[arm_index]

        # Group results by control_id.
        by_control: dict[str, tuple[int, int]] = {}  # control_id -> (n_new, s_new)
        for pr in probe_results:
            cid = pr["control_id"]
            n_prev, s_prev = by_control.get(cid, (0, 0))
            by_control[cid] = (n_prev + 1, s_prev + (1 if pr["passed"] else 0))

        # Compute total information gain across all mandatory controls touched.
        total_ig: float = 0.0
        for cid, (n_new, s_new) in by_control.items():
            ctrl = self._control_map.get(cid)
            if ctrl is not None and ctrl.is_mandatory:
                total_ig += ctrl.information_gain(n_new, s_new)

        # Normalise into [0, 1].
        k_mandatory = max(len(self._mandatory_controls), 1)
        normalised_reward = min(total_ig / k_mandatory, 1.0)

        # Update control states.
        for cid, (n_new, s_new) in by_control.items():
            ctrl = self._control_map.get(cid)
            if ctrl is not None:
                ctrl.n += n_new
                ctrl.s += s_new

        # Update arm state.
        arm.pulls += 1
        arm.total_reward += normalised_reward
        self._step += 1
        self._total_queries += len(probe_results)

        # Build posterior state snapshot.
        posterior: dict[str, dict] = {
            a.suite_id: a.to_posterior_snapshot() for a in self._arms
        }

        t = self._step
        return ArmPull(
            step=self._step,
            suite_id=arm.suite_id,
            arm_index=arm_index,
            reward=round(normalised_reward, 6),
            ucb_value=round(arm.ucb_value(t, self._exploration_constant), 6),
            posterior_state=posterior,
            cumulative_queries=self._total_queries,
        )

    # ---------------------------------------------------------------------------
    # Synchronous run loop (used directly in tests)
    # ---------------------------------------------------------------------------

    def run_sync(
        self,
        suite_runner: Callable[[str, list[str]], list[dict]],
    ) -> tuple[list[ArmPull], str, str]:
        """Run the bandit evaluation synchronously until a stopping criterion is met.

        This is the canonical evaluation loop. It is synchronous so that tests
        can call it without an event loop. The async wrapper run_async() delegates
        here and layers DB writes and streaming on top.

        Args:
            suite_runner: Callable(suite_id, control_ids) -> list of probe result dicts.
                          Each probe result dict must have at minimum:
                            control_id: str
                            probe_id:   str
                            passed:     bool
                            score:      float

        Returns:
            (arm_pulls, stopping_reason, verdict)
        """
        arm_pulls: list[ArmPull] = []

        while True:
            should_stop, reason = self.check_stopping()
            if should_stop:
                stopping_reason = reason or "budget_exhausted"
                break

            arm_idx = self.select_arm()
            suite_id = self._arms[arm_idx].suite_id

            # Collect control_ids for mandatory controls covered by this suite.
            control_ids = [
                c.control_id
                for c in self._controls_by_suite.get(suite_id, [])
                if c.is_mandatory and not self._is_mandatory_control_decided(c)
            ]
            if not control_ids:
                # No undecided mandatory controls; this arm should have been skipped.
                # Check stopping again (a concurrent update may have decided everything).
                continue

            probes = suite_runner(suite_id, control_ids)
            arm_pull = self.pull(arm_idx, probes)
            arm_pulls.append(arm_pull)

        verdict = self.final_verdict()
        return arm_pulls, stopping_reason, verdict

    # ---------------------------------------------------------------------------
    # Async run loop (for production use with DB writes and streaming)
    # ---------------------------------------------------------------------------

    async def run_async(
        self,
        suite_runner: Callable[[str, list[str]], list[dict]],
        event_callback: Callable | None = None,
    ) -> tuple[list[ArmPull], str, str]:
        """Async wrapper around run_sync.

        Executes the synchronous loop in the current thread (the evaluation
        runs fast enough that blocking asyncio is acceptable in the demo;
        Wave 3 may move to asyncio.to_thread if needed).

        Args:
            suite_runner:   Same as run_sync.
            event_callback: Optional callable(event_dict) invoked after each arm
                            pull and probe batch. Wave 3 HARNESS wires this to the
                            WebSocket emitter.

        Returns:
            (arm_pulls, stopping_reason, verdict)
        """
        # SOVEREIGN-TODO (Wave 3): replace with asyncio.to_thread when the
        # suite runner itself becomes async (live model endpoint calls).
        arm_pulls, stopping_reason, verdict = self.run_sync(suite_runner)
        return arm_pulls, stopping_reason, verdict

    # ---------------------------------------------------------------------------
    # Introspection (for debugging and tests)
    # ---------------------------------------------------------------------------

    def control_states(self) -> dict[str, dict]:
        """Return a snapshot of all control states for inspection.

        The returned dict per control includes:
            n               -- probes conducted
            s               -- probes that returned passed=True
            p_hat           -- empirical pass rate
            required_pass_rate -- derived from pass_threshold
            is_mandatory    -- whether the control gates certification
            is_zero_tolerance -- True when required_pass_rate == 1.0
            decided         -- whether a decision has been reached
            decision        -- True (pass), False (fail), or None (undecided)
            decision_basis  -- one of the six decision-basis constants, or None
            violation_rate_bound -- Clopper-Pearson upper bound on violation rate
                                    for zero-tolerance controls after a clean run;
                                    None otherwise.
        """
        result: dict[str, dict] = {}
        for ctrl in self._controls:
            basis = ctrl.current_decision_basis()
            is_clean_run = (ctrl.is_zero_tolerance and ctrl.n > 0 and ctrl.s == ctrl.n)
            lower_bound = ctrl.achieved_pass_rate_lower_bound()
            result[ctrl.control_id] = {
                "n": ctrl.n,
                "s": ctrl.s,
                "p_hat": round(ctrl.p_hat, 6),
                "required_pass_rate": ctrl.required_pass_rate,
                "is_mandatory": ctrl.is_mandatory,
                "is_zero_tolerance": ctrl.is_zero_tolerance,
                "decided": basis is not None,
                "decision": ctrl.decision(),
                "decision_basis": basis,
                "n_max": ctrl.n_max,
                "alpha_per_control": ctrl.alpha_per_control,
                # achieved_pass_rate_lower_bound: exact one-sided CP lower bound on the
                # true pass rate at alpha_per_control significance, on a clean run (s==n).
                # Present for both STATISTICAL_PASS (where it exceeds required_pass_rate)
                # and BUDGET_PASS (where it does not). A certificate reader must be able
                # to see the actual statistical strength regardless of decision basis.
                # None when n==0 or when some probes failed (partial-failure lower bound
                # requires scipy; not relevant for adverse decisions).
                "achieved_pass_rate_lower_bound": (
                    round(lower_bound, 6) if lower_bound is not None else None
                ),
                # violation_rate_bound: retained for zero-tolerance CLEAN_RUN_BOUNDED
                # controls only. For non-zero-tolerance controls use
                # achieved_pass_rate_lower_bound instead.
                "violation_rate_bound": (
                    round(ctrl.violation_rate_upper_bound(), 6)
                    if is_clean_run
                    else None
                ),
            }
        return result

    @property
    def total_queries(self) -> int:
        return self._total_queries

    @property
    def step(self) -> int:
        return self._step
