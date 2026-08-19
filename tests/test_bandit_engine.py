"""Wave 1 acceptance tests for the BANDIT engine.

Coverage:
  1. Determinism under fixed seed: same arm-pull sequence every run.
  2. Different seed produces a different sequence (anti-vacuity).
  3. Decision parity: adaptive and exhaustive reach identical verdicts.
  4. Hoeffding stopping: FAIL detected before budget exhaustion.
  5. Advisory controls do not gate the verdict.
  6. MCSS: ordering improves with accumulated evaluations.
  7. Required-pass-rate derivation for rate-type and error-rate-type thresholds.

All tests use the fixture in tests/fixtures/bandit_test_controls.json.
That file is labelled TEST FIXTURE ONLY and contains no governance content.

Suite runner: MockSuiteRunner. Probe outcomes are pre-configured at
construction. The runner is deterministic: same control_id always yields the
same outcome. The engine's RNG provides any tie-breaking needed by UCB1.
"""

from __future__ import annotations

import json
import pathlib
import tempfile

import pytest

from mizan.engine.bandit.allocator import (
    BUDGET_PASS,
    CLEAN_RUN_BOUNDED,
    STATISTICAL_FAIL,
    STATISTICAL_PASS,
    ZERO_VIOLATION_FAIL,
    BanditEngine,
    ControlState,
    _derive_required_pass_rate,
    _min_probes_for_statistical_pass,
)
from mizan.engine.mcss.searcher import MCSSLayer

# ---------------------------------------------------------------------------
# Load test fixture
# ---------------------------------------------------------------------------

_FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "bandit_test_controls.json"


def _load_fixture() -> dict:
    with _FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _fixture_engine(
    seed: int = 42,
    outcomes: dict[str, bool] | None = None,
    probes_per_pull: int = 5,
    n_max: int = 20,
) -> tuple[BanditEngine, "MockSuiteRunner"]:
    """Construct a BanditEngine from the test fixture with a mock runner."""
    data = _load_fixture()
    runner = MockSuiteRunner(
        outcomes=outcomes or {
            "fixture-ctrl-safety-001":       True,
            "fixture-ctrl-safety-002":       True,
            "fixture-ctrl-bias-001":         True,
            "fixture-ctrl-transparency-001": True,
            "fixture-ctrl-advisory-001":     True,
        },
        probes_per_pull=probes_per_pull,
    )
    engine = BanditEngine(
        evaluation_id="test-eval-id",
        use_case_class=data["use_case_class"],
        confidence_threshold=data["confidence_threshold"],
        controls=data["controls"],
        engine_config={
            "random_seed": seed,
            "n_max_per_control": n_max,
            "total_budget": 500,
        },
    )
    return engine, runner


# ---------------------------------------------------------------------------
# Mock suite runner (TEST FIXTURE ONLY)
# ---------------------------------------------------------------------------

class MockSuiteRunner:
    """Deterministic suite runner for tests.

    TEST FIXTURE ONLY. Not for production use. Probe outcomes are configured
    at construction; every probe for a given control_id returns the same
    passed/failed result consistently.
    """

    def __init__(
        self,
        outcomes: dict[str, bool],
        probes_per_pull: int = 5,
    ) -> None:
        self.outcomes = outcomes
        self.probes_per_pull = probes_per_pull
        self.calls: list[tuple[str, list[str]]] = []

    def __call__(self, suite_id: str, control_ids: list[str]) -> list[dict]:
        """Return deterministic probe results for all supplied control_ids."""
        self.calls.append((suite_id, list(control_ids)))
        results: list[dict] = []
        for ctrl_id in control_ids:
            passed = self.outcomes.get(ctrl_id, True)
            score = 1.0 if passed else 0.0
            for probe_n in range(self.probes_per_pull):
                probe_id = f"{suite_id}-{ctrl_id}-{probe_n}"
                results.append({
                    "control_id": ctrl_id,
                    "probe_id": probe_id,
                    "suite_id": suite_id,
                    "score": score,
                    "passed": passed,
                    "payload": {
                        "probe_id": probe_id,
                        "suite_id": suite_id,
                        "control_id": ctrl_id,
                        "locale": "en",
                        "prompt": f"fixture prompt for {ctrl_id}",
                        "response": "fixture response",
                        "scorer": "mock_v1",
                        "score": score,
                        "passed": passed,
                        "scorer_metadata": {"fixture": True},
                    },
                })
        return results


# ---------------------------------------------------------------------------
# Helper: exhaustive evaluation (for parity test)
# ---------------------------------------------------------------------------

def run_exhaustive(
    controls: list[dict],
    runner: MockSuiteRunner,
    n_probes_per_control: int = 20,
) -> str:
    """Run every mandatory control fully and return 'certified' or 'rejected'.

    This is the baseline against which MIZAN's adaptive verdict is compared.
    It does not use UCB1 or Hoeffding: it runs all mandatory controls to full
    budget and decides purely from empirical pass rates.
    """
    mandatory = [c for c in controls if c["is_mandatory"]]
    control_decisions: dict[str, bool] = {}

    # Group mandatory controls by suite.
    suites: dict[str, list[str]] = {}
    for c in mandatory:
        suites.setdefault(c["suite_id"], []).append(c["control_id"])

    # Run each suite and accumulate pass counts.
    counts: dict[str, tuple[int, int]] = {}  # control_id -> (n, s)
    for suite_id, ctrl_ids in suites.items():
        # Run n_probes_per_control probes for each control in the suite.
        old_ppp = runner.probes_per_pull
        runner.probes_per_pull = n_probes_per_control
        probes = runner(suite_id, ctrl_ids)
        runner.probes_per_pull = old_ppp
        for pr in probes:
            cid = pr["control_id"]
            n, s = counts.get(cid, (0, 0))
            counts[cid] = (n + 1, s + (1 if pr["passed"] else 0))

    # Decide each mandatory control.
    for c in mandatory:
        cid = c["control_id"]
        n, s = counts.get(cid, (0, 0))
        p_hat = s / n if n > 0 else 0.0
        required = _derive_required_pass_rate(float(c["pass_threshold"]))
        control_decisions[cid] = p_hat >= required

    return "certified" if all(control_decisions.values()) else "rejected"


# ---------------------------------------------------------------------------
# Test 1: Determinism under fixed seed
# ---------------------------------------------------------------------------

def test_determinism_same_seed() -> None:
    """Two runs with the same seed must produce byte-identical arm-pull sequences.

    This is a hard requirement: the pitch depends on deterministic reproduction
    of results, and the Wave 2 proof script requires it.
    """
    data = _load_fixture()

    def _run(seed: int) -> list[tuple[int, str, float]]:
        engine, runner = _fixture_engine(seed=seed, n_max=20)
        arm_pulls, _, _ = engine.run_sync(runner)
        return [(p.step, p.suite_id, p.reward) for p in arm_pulls]

    run_a = _run(42)
    run_b = _run(42)

    assert len(run_a) > 0, "Engine produced no arm pulls."
    assert run_a == run_b, (
        "Arm-pull sequence differed between two runs with the same seed. "
        "All randomness must flow through the seeded numpy.random.Generator."
    )


# ---------------------------------------------------------------------------
# Test 2: Different seed produces a different sequence (anti-vacuity)
# ---------------------------------------------------------------------------

def test_different_seed_produces_different_sequence() -> None:
    """A different seed must yield a different arm-pull sequence.

    This test prevents the determinism test from passing vacuously (i.e.,
    an engine that always produces the same output regardless of seed would
    satisfy test 1 trivially).

    Note: if the fixture has only two suites and UCB1 always pulls them in
    the same strict order (no tie-breaking needed), seeds may not diverge.
    The fixture is designed with two suites so that UCB1 tie-breaking occurs
    after both are initially explored; varying the seed changes UCB1 selections.
    The fixture uses n_max=20 and probes_per_pull=5 to create enough arms
    pulls for UCB1 to operate.
    """
    def _run(seed: int) -> list[tuple[int, str, float]]:
        engine, runner = _fixture_engine(seed=seed, n_max=20, probes_per_pull=5)
        arm_pulls, _, _ = engine.run_sync(runner)
        return [(p.step, p.suite_id, p.reward) for p in arm_pulls]

    run_seed_42 = _run(42)
    run_seed_99 = _run(99)

    assert len(run_seed_42) > 0
    assert len(run_seed_99) > 0
    # With two suites, UCB1 pulls both once deterministically (warm-start)
    # and then allocates by mean reward. If both have the same mean after
    # the warm-start, tie-breaking by RNG produces different sequences for
    # different seeds. The test asserts at least one step differs.
    assert run_seed_42 != run_seed_99, (
        "Arm-pull sequences were identical for seed 42 and seed 99. "
        "Check that the fixture creates genuine UCB1 tie-breaking and that "
        "the engine uses self._rng (not a global) for tie-breaking."
    )


# ---------------------------------------------------------------------------
# Test 3: Decision parity with exhaustive evaluation (all-pass scenario)
# ---------------------------------------------------------------------------

def test_decision_parity_all_pass() -> None:
    """Adaptive verdict must match exhaustive verdict when all controls pass.

    This is a charter requirement: a reduction figure with a different verdict
    is worthless, and worse than worthless in a compliance product.
    """
    data = _load_fixture()
    outcomes = {
        "fixture-ctrl-safety-001":       True,
        "fixture-ctrl-safety-002":       True,
        "fixture-ctrl-zt-001":           True,
        "fixture-ctrl-bias-001":         True,
        "fixture-ctrl-transparency-001": True,
        "fixture-ctrl-advisory-001":     True,
    }
    engine, runner = _fixture_engine(seed=42, outcomes=outcomes, n_max=20)
    _, _, adaptive_verdict = engine.run_sync(runner)

    exhaustive_runner = MockSuiteRunner(outcomes=outcomes, probes_per_pull=20)
    exhaustive_verdict = run_exhaustive(data["controls"], exhaustive_runner, n_probes_per_control=20)

    assert adaptive_verdict == exhaustive_verdict == "certified", (
        f"Parity failure: adaptive={adaptive_verdict}, exhaustive={exhaustive_verdict}. "
        "The engine must reach the same verdict as exhaustive evaluation."
    )


# ---------------------------------------------------------------------------
# Test 4: Decision parity with exhaustive evaluation (fail scenario)
# ---------------------------------------------------------------------------

def test_decision_parity_mandatory_fail() -> None:
    """Adaptive verdict must match exhaustive verdict when a mandatory control fails.

    The engine must detect the failure and stop; it must not certify a model
    that exhaustive evaluation would reject.
    """
    data = _load_fixture()
    outcomes = {
        "fixture-ctrl-safety-001":       False,  # mandatory, will cause rejection
        "fixture-ctrl-safety-002":       True,
        "fixture-ctrl-zt-001":           True,
        "fixture-ctrl-bias-001":         True,
        "fixture-ctrl-transparency-001": True,
        "fixture-ctrl-advisory-001":     True,
    }
    engine, runner = _fixture_engine(seed=42, outcomes=outcomes, n_max=20)
    arm_pulls, stopping_reason, adaptive_verdict = engine.run_sync(runner)

    exhaustive_runner = MockSuiteRunner(outcomes=outcomes, probes_per_pull=20)
    exhaustive_verdict = run_exhaustive(data["controls"], exhaustive_runner, n_probes_per_control=20)

    assert adaptive_verdict == exhaustive_verdict == "rejected", (
        f"Parity failure: adaptive={adaptive_verdict}, exhaustive={exhaustive_verdict}."
    )


# ---------------------------------------------------------------------------
# Test 5: Hoeffding-based early stopping on mandatory control failure
# ---------------------------------------------------------------------------

def test_hoeffding_early_stop_on_fail() -> None:
    """Engine must stop before budget exhaustion when a mandatory control fails decisively.

    With all probes for a control returning failed (p_hat = 0.0) and a
    required pass rate of 0.90, the Hoeffding FAIL condition triggers when
    0.0 + eps(n) < 0.90. This happens at a small n, well before n_max = 50.
    """
    outcomes = {
        "fixture-ctrl-safety-001":       False,  # decisive failure (p_hat = 0.0)
        "fixture-ctrl-safety-002":       True,
        "fixture-ctrl-bias-001":         True,
        "fixture-ctrl-transparency-001": True,
        "fixture-ctrl-advisory-001":     True,
    }
    # Use a larger n_max to confirm we stop well before the budget.
    engine, runner = _fixture_engine(seed=42, outcomes=outcomes, n_max=50, probes_per_pull=5)
    arm_pulls, stopping_reason, verdict = engine.run_sync(runner)

    assert verdict == "rejected"
    assert stopping_reason == "mandatory_control_failed", (
        f"Expected 'mandatory_control_failed', got '{stopping_reason}'. "
        "The engine should stop as soon as Hoeffding detects a decisive failure, "
        "not wait for the budget to be exhausted."
    )
    # Verify early stop: total queries should be far fewer than n_max probes
    # per mandatory control (50 * 3 = 150 for 3 mandatory controls).
    assert engine.total_queries < 100, (
        f"Engine ran {engine.total_queries} queries before stopping. "
        "Early stopping should have triggered within ~30 queries of the failing control."
    )


# ---------------------------------------------------------------------------
# Test 6: Advisory controls do not gate the verdict
# ---------------------------------------------------------------------------

def test_advisory_control_does_not_gate_verdict() -> None:
    """A failing advisory control must not cause rejection.

    Advisory controls (is_mandatory=False) carry weight 0.0 and must not
    influence the certification verdict. The engine skips them in Phase 1
    arm selection. The verdict is determined solely by mandatory controls.
    """
    outcomes = {
        "fixture-ctrl-safety-001":       True,
        "fixture-ctrl-safety-002":       True,
        "fixture-ctrl-zt-001":           True,
        "fixture-ctrl-bias-001":         True,
        "fixture-ctrl-transparency-001": True,
        "fixture-ctrl-advisory-001":     False,  # advisory fails; must not affect verdict
    }
    engine, runner = _fixture_engine(seed=42, outcomes=outcomes, n_max=20)
    _, _, verdict = engine.run_sync(runner)

    assert verdict == "certified", (
        f"Got verdict '{verdict}' but mandatory controls all pass. "
        "A failing advisory control must not cause rejection."
    )

    # The advisory control should not have been probed during Phase 1
    # (since its arm has no undecided mandatory controls for the engine
    # to pull it for).
    advisory_id = "fixture-ctrl-advisory-001"
    ctrl_state = engine.control_states()
    advisory_state = ctrl_state.get(advisory_id, {})
    # The advisory control lives in fixture-suite-bias alongside a mandatory control.
    # The engine pulls fixture-suite-bias for the mandatory ctrl-bias-001 but
    # explicitly filters advisory controls from the control_ids passed to the runner.
    # So the advisory control's n should remain 0.
    assert advisory_state["n"] == 0, (
        f"Advisory control was probed during Phase 1 (n={advisory_state['n']}). "
        "Advisory controls must not be probed in the mandatory-evaluation phase."
    )


# ---------------------------------------------------------------------------
# Test 7: Required-pass-rate derivation
# ---------------------------------------------------------------------------

def test_required_pass_rate_rate_type() -> None:
    """Rate-type threshold in [0.5, 1.0] maps directly to required_pass_rate."""
    assert _derive_required_pass_rate(0.95) == pytest.approx(0.95)
    assert _derive_required_pass_rate(0.85) == pytest.approx(0.85)
    assert _derive_required_pass_rate(1.0) == pytest.approx(1.0)
    assert _derive_required_pass_rate(0.5) == pytest.approx(0.5)


def test_required_pass_rate_error_rate_type() -> None:
    """Error-rate-type threshold in [0, 0.5) maps to 1 - threshold."""
    assert _derive_required_pass_rate(0.1) == pytest.approx(0.9)
    assert _derive_required_pass_rate(0.03) == pytest.approx(0.97)
    assert _derive_required_pass_rate(0.02) == pytest.approx(0.98)
    assert _derive_required_pass_rate(0.05) == pytest.approx(0.95)


def test_required_pass_rate_non_bernoulli_scale() -> None:
    """Non-Bernoulli-scale threshold (> 1.0) maps to the default of 0.8."""
    assert _derive_required_pass_rate(4.0) == pytest.approx(0.8)
    assert _derive_required_pass_rate(10.0) == pytest.approx(0.8)


def test_required_pass_rate_threshold_direction_at_least() -> None:
    """threshold_direction='at_least' maps pass_threshold directly to required_pass_rate."""
    assert _derive_required_pass_rate(0.90, threshold_direction="at_least") == pytest.approx(0.90)
    assert _derive_required_pass_rate(0.97, threshold_direction="at_least") == pytest.approx(0.97)
    assert _derive_required_pass_rate(1.0,  threshold_direction="at_least") == pytest.approx(1.0)


def test_required_pass_rate_threshold_direction_at_most() -> None:
    """threshold_direction='at_most' maps pass_threshold to 1 - pass_threshold.

    This is the correct, unambiguous path for error-rate-type controls: a control
    that must have a violation rate at most 0.15 requires a pass rate of at least 0.85.
    No magnitude heuristic is needed when threshold_direction is explicit.
    """
    assert _derive_required_pass_rate(0.15, threshold_direction="at_most") == pytest.approx(0.85)
    assert _derive_required_pass_rate(0.02, threshold_direction="at_most") == pytest.approx(0.98)
    assert _derive_required_pass_rate(0.40, threshold_direction="at_most") == pytest.approx(0.60)


# ---------------------------------------------------------------------------
# Test 8: Per-control n_max derivation
# ---------------------------------------------------------------------------

def test_per_control_n_max_derivation() -> None:
    """Verify per-control n_max is derived from the coordinator's formula.

    For K=5 mandatory controls, conf=0.95:
        alpha_per_control = (1 - 0.95) / 5 = 0.01

    For fixture-ctrl-safety-001 (required_pass_rate=0.90):
        n_min = ceil(ln(0.01) / ln(0.90))
               = ceil(-4.60517 / -0.10536)
               = ceil(43.7) = 44

    When _fixture_engine is called with n_max=20 (a cap), the engine applies
    min(derived, cap), so ctrl.n_max = min(44, 20) = 20.

    The per-control delta_corrected must follow alpha_per_control / n_max.

    This test also verifies _min_probes_for_statistical_pass directly.
    """
    import math

    data = _load_fixture()
    k_mandatory = sum(1 for c in data["controls"] if c["is_mandatory"])
    confidence_threshold = data["confidence_threshold"]
    alpha_per_control = (1.0 - confidence_threshold) / k_mandatory

    # Direct formula verification for safety-001 (r=0.90).
    n_min_s001 = _min_probes_for_statistical_pass(0.90, alpha_per_control)
    expected_n_min = math.ceil(math.log(alpha_per_control) / math.log(0.90))
    assert n_min_s001 == expected_n_min, (
        f"_min_probes_for_statistical_pass(0.90, {alpha_per_control}) = {n_min_s001}, "
        f"expected {expected_n_min}. Check the formula in allocator.py."
    )
    # n_min must be >= 44 for r=0.90, alpha=0.01
    assert n_min_s001 >= 44, (
        f"n_min for r=0.90, alpha=0.01 should be >=44, got {n_min_s001}."
    )

    # Engine applies the cap correctly.
    cap = 20
    engine, _ = _fixture_engine(seed=42, n_max=cap)
    states = engine.control_states()
    s001 = states["fixture-ctrl-safety-001"]
    # cap < derived n_min, so n_max should equal the cap.
    assert s001["n_max"] == cap, (
        f"n_max for safety-001 should be capped at {cap}, got {s001['n_max']}. "
        "The engine must apply min(derived, cap)."
    )
    # alpha_per_control must equal (1-conf)/K.
    assert s001["alpha_per_control"] == pytest.approx(alpha_per_control, rel=1e-9), (
        f"alpha_per_control={s001['alpha_per_control']}, expected {alpha_per_control}."
    )


# ---------------------------------------------------------------------------
# Test 9: Control-state entropy computations
# ---------------------------------------------------------------------------

def test_binary_entropy_extremes() -> None:
    """H(0) and H(1) must be 0; H(0.5) must be 1."""
    assert ControlState.binary_entropy(0.0) == pytest.approx(0.0)
    assert ControlState.binary_entropy(1.0) == pytest.approx(0.0)
    assert ControlState.binary_entropy(0.5) == pytest.approx(1.0)


def test_information_gain_decreases_on_consistent_evidence() -> None:
    """Information gain is positive when evidence reduces entropy."""
    ctrl = ControlState(
        control_id="test",
        suite_id="test-suite",
        is_mandatory=True,
        required_pass_rate=0.90,
    )
    # Before any probes: p_hat = 0.5, H = 1.0
    h_before = ctrl.binary_entropy(ctrl.p_hat)
    assert h_before == pytest.approx(1.0)

    # All 5 probes pass: p_hat moves toward 1.0
    ig = ctrl.information_gain(n_new=5, s_new=5)
    assert ig > 0.0, "Information gain must be positive when evidence reduces entropy."


# ---------------------------------------------------------------------------
# Test 10: MCSS ordering improves with accumulated evaluations
# ---------------------------------------------------------------------------

def test_mcss_ordering_improves_over_evaluations() -> None:
    """MCSS ordering must reflect accumulated reward statistics.

    After one evaluation where fixture-suite-safety earned higher mean
    reward than fixture-suite-bias, get_suite_ordering must place
    fixture-suite-safety first.

    This is the compounding claim: the registry gets faster over evaluations
    because the warm-start ordering improves.
    """
    suite_ids = ["fixture-suite-safety", "fixture-suite-bias"]

    # Simulate two evaluations: safety yields higher reward per pull.
    from mizan.api.schemas import ArmPull
    pulls_eval1 = [
        ArmPull(
            step=1,
            suite_id="fixture-suite-safety",
            arm_index=0,
            reward=0.8,
            ucb_value=1.5,
            posterior_state={},
            cumulative_queries=5,
        ),
        ArmPull(
            step=2,
            suite_id="fixture-suite-bias",
            arm_index=1,
            reward=0.3,
            ucb_value=1.2,
            posterior_state={},
            cumulative_queries=10,
        ),
    ]

    layer = MCSSLayer.fresh("fixture_test_case", suite_ids)
    assert layer.total_evaluations == 0

    layer.update(pulls_eval1)
    assert layer.total_evaluations == 1

    ordering = layer.get_suite_ordering()
    assert ordering[0] == "fixture-suite-safety", (
        f"Expected fixture-suite-safety first (higher mean reward), got: {ordering}. "
        "MCSS ordering must reflect accumulated statistics."
    )


def test_mcss_convergence_delta_zero_on_stable_ordering() -> None:
    """convergence_delta must return 0.0 when the ordering has not changed."""
    layer = MCSSLayer.fresh("fixture_test_case", ["suite-a", "suite-b", "suite-c"])
    ordering_before = ["suite-a", "suite-b", "suite-c"]
    # Simulate no change (layer has no statistics, gets same order as fresh).
    delta = layer.convergence_delta(ordering_before)
    # Two orderings with no historical data both produce the original order.
    assert delta == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Test 11: MCSS persistence round-trip (sync path, test-only)
# ---------------------------------------------------------------------------

def test_mcss_sync_round_trip() -> None:
    """Save and reload MCSS state via the test-only sync path."""
    suite_ids = ["suite-alpha", "suite-beta"]
    layer = MCSSLayer.fresh("round_trip_test", suite_ids)
    from mizan.api.schemas import ArmPull
    layer.update([
        ArmPull(
            step=1,
            suite_id="suite-alpha",
            arm_index=0,
            reward=0.6,
            ucb_value=1.0,
            posterior_state={},
            cumulative_queries=5,
        ),
    ])

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
        db_path = fh.name

    # Initialise schema.
    import sqlite3
    import pathlib
    schema_path = pathlib.Path(__file__).parents[1] / "engine" / "db" / "schema.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))

    layer.save_sync(db_path)
    loaded = MCSSLayer.load_sync("round_trip_test", suite_ids, db_path)

    assert loaded.total_evaluations == 1
    assert "suite-alpha" in loaded.arm_statistics
    assert loaded.arm_statistics["suite-alpha"]["mean_reward"] == pytest.approx(0.6)
    # Ordering: suite-alpha has higher mean reward than suite-beta (unseen).
    assert loaded.get_suite_ordering()[0] == "suite-alpha"


# ---------------------------------------------------------------------------
# Test 12: Zero-tolerance control immediate fail on any violation
# ---------------------------------------------------------------------------

def test_zero_tolerance_any_violation_causes_immediate_fail() -> None:
    """Zero-tolerance control: any observed violation yields ZERO_VIOLATION_FAIL.

    For a control with required_pass_rate == 1.0, even a single observed
    failure is a certain, immediate fail: the true violation rate is >= 1/n > 0,
    which refutes the zero-tolerance requirement. No confidence budget is needed;
    the observation is decisive on its own.
    """
    ctrl = ControlState(
        control_id="test-zt",
        suite_id="test-suite",
        is_mandatory=True,
        required_pass_rate=1.0,
    )
    assert ctrl.is_zero_tolerance

    # Set the per-control budget fields (normally set by BanditEngine.__init__).
    ctrl.delta_corrected = 0.001
    ctrl.n_max = 20

    # Before any probes: undecided.
    assert ctrl.current_decision_basis() is None

    # One violation out of three probes: immediate fail.
    ctrl.n = 3
    ctrl.s = 2
    basis = ctrl.current_decision_basis()
    assert basis == ZERO_VIOLATION_FAIL, (
        f"Expected ZERO_VIOLATION_FAIL, got {basis!r}. "
        "Any observed violation for a zero-tolerance control is an immediate, certain fail."
    )
    assert ctrl.decision() is False


# ---------------------------------------------------------------------------
# Test 13: Violation rate upper bound formula
# ---------------------------------------------------------------------------

def test_violation_rate_upper_bound_formula() -> None:
    """violation_rate_upper_bound follows the exact Clopper-Pearson formula.

    With 0 violations in n probes, p_upper = 1 - delta_corrected^(1/n).
    This is the exact one-sided beta-distribution bound, not the rule-of-three
    approximation (which converges to the same value for small delta_corrected).
    """
    ctrl = ControlState(
        control_id="test-zt",
        suite_id="test-suite",
        is_mandatory=True,
        required_pass_rate=1.0,
    )
    # Set the per-control delta_corrected field (normally set by BanditEngine.__init__).
    delta_corrected = 0.0005
    ctrl.delta_corrected = delta_corrected

    # No probes: bound is 1.0 (no information).
    ctrl.n = 0
    ctrl.s = 0
    assert ctrl.violation_rate_upper_bound() == pytest.approx(1.0)

    # After 20 clean probes: exact Clopper-Pearson bound.
    ctrl.n = 20
    ctrl.s = 20
    expected = 1.0 - (delta_corrected ** (1.0 / 20))
    assert ctrl.violation_rate_upper_bound() == pytest.approx(expected)
    # At n=20, delta=0.0005, the bound should be well below 50 percent.
    assert expected < 0.5, (
        f"Bound {expected:.4f} should be < 0.5 at n=20, delta={delta_corrected}. "
        "Check the Clopper-Pearson formula."
    )

    # Bound tightens monotonically as n increases.
    ctrl.n = 50
    ctrl.s = 50
    bound_at_50 = ctrl.violation_rate_upper_bound()
    assert bound_at_50 < expected, (
        "Violation rate bound must tighten as n increases (more probes, stronger bound)."
    )


# ---------------------------------------------------------------------------
# Test 14: Per-control decision basis after certified evaluation
# ---------------------------------------------------------------------------

def test_decision_basis_per_control_type() -> None:
    """After a certified evaluation, each control carries the correct decision basis.

    Zero-tolerance control (zt-001, required_pass_rate=1.0):
        All probes pass -> CLEAN_RUN_BOUNDED at budget exhaustion.
        The violation_rate_bound is the Clopper-Pearson upper bound.

    Non-zero-tolerance control (safety-001, required_pass_rate=0.90):
        All probes pass, but the CP lower bound PASS condition cannot fire at
        n_max=20 (derived budget requires 44 probes; the test cap is 20).
        The exact CP lower bound at n=20: p_lower = 0.01^(1/20) ≈ 0.794,
        which is below required_pass_rate=0.90, so STATISTICAL_PASS is not
        asserted. The control lands on BUDGET_PASS: budget exhausted,
        p_hat >= required_pass_rate, no statistical guarantee.

    This is the critical honesty property the coordinator required. BUDGET_PASS
    must be labelled explicitly on every certificate; it is not a statistical
    guarantee.
    """
    engine, runner = _fixture_engine(seed=42, n_max=20)
    _, _, verdict = engine.run_sync(runner)
    assert verdict == "certified"

    states = engine.control_states()

    # Zero-tolerance control must be CLEAN_RUN_BOUNDED.
    zt = states["fixture-ctrl-zt-001"]
    assert zt["is_zero_tolerance"]
    assert zt["decision_basis"] == CLEAN_RUN_BOUNDED, (
        f"Expected {CLEAN_RUN_BOUNDED!r} for zero-tolerance control, "
        f"got {zt['decision_basis']!r}. "
        "A clean run of a zero-tolerance control is bounded, not statistically certified."
    )
    assert zt["violation_rate_bound"] is not None, (
        "violation_rate_bound must be populated for CLEAN_RUN_BOUNDED decisions."
    )
    assert zt["violation_rate_bound"] < 0.5, (
        f"Violation rate bound {zt['violation_rate_bound']} is implausibly large at n=20."
    )

    # Non-zero-tolerance passing control must be BUDGET_PASS, not STATISTICAL_PASS.
    s001 = states["fixture-ctrl-safety-001"]
    assert not s001["is_zero_tolerance"]
    assert s001["decision_basis"] == BUDGET_PASS, (
        f"Expected {BUDGET_PASS!r} for safety-001 at n_max=20, "
        f"got {s001['decision_basis']!r}. "
        "The CP lower bound PASS requires 44 probes (derived) for required_pass_rate=0.90; "
        "the test cap is 20, so p_lower=0.01^(1/20)~=0.794 < 0.90 and STATISTICAL_PASS "
        "cannot fire. At n_max=20 this control can only be decided via BUDGET_PASS, "
        "which carries no statistical guarantee."
    )
    assert s001["violation_rate_bound"] is None, (
        "violation_rate_bound must be None for non-zero-tolerance controls."
    )

    # The achieved lower bound must be present and show honest strength.
    # safety-001: all probes pass (s==n==20), so lower bound = 0.01^(1/20).
    import math as _math
    expected_lower = 0.01 ** (1.0 / s001["n"])
    assert s001["achieved_pass_rate_lower_bound"] is not None, (
        "achieved_pass_rate_lower_bound must be present for a clean-run BUDGET_PASS."
    )
    assert s001["achieved_pass_rate_lower_bound"] == pytest.approx(expected_lower, rel=1e-6), (
        f"Lower bound {s001['achieved_pass_rate_lower_bound']:.4f} does not match "
        f"expected {expected_lower:.4f}. Certificate readers must see the exact CP "
        "lower bound achieved, not only the BUDGET_PASS label."
    )
    assert s001["achieved_pass_rate_lower_bound"] < s001["required_pass_rate"], (
        "BUDGET_PASS lower bound must be below required_pass_rate; otherwise the "
        "control would have been decided STATISTICAL_PASS."
    )


# ---------------------------------------------------------------------------
# Test 15: Zero-violation fail fires immediately via the engine
# ---------------------------------------------------------------------------

def test_engine_stops_immediately_on_zero_tolerance_violation() -> None:
    """The engine stops as soon as a zero-tolerance violation is observed.

    fixture-ctrl-zt-001 (required_pass_rate=1.0) is in suite-safety. If its
    probe returns False, the engine must detect ZERO_VIOLATION_FAIL and stop
    before the budget is exhausted.
    """
    outcomes = {
        "fixture-ctrl-safety-001":       True,
        "fixture-ctrl-safety-002":       True,
        "fixture-ctrl-zt-001":           False,   # one violation -> immediate ZERO_VIOLATION_FAIL
        "fixture-ctrl-bias-001":         True,
        "fixture-ctrl-transparency-001": True,
        "fixture-ctrl-advisory-001":     True,
    }
    engine, runner = _fixture_engine(seed=42, outcomes=outcomes, n_max=50)
    _, stopping_reason, verdict = engine.run_sync(runner)

    assert verdict == "rejected", (
        f"Expected 'rejected' when zero-tolerance control has a violation, got {verdict!r}."
    )
    assert stopping_reason == "mandatory_control_failed", (
        f"Expected 'mandatory_control_failed', got {stopping_reason!r}. "
        "ZERO_VIOLATION_FAIL must trigger the same stopping reason as other mandatory failures."
    )

    zt_state = engine.control_states()["fixture-ctrl-zt-001"]
    assert zt_state["decision_basis"] == ZERO_VIOLATION_FAIL, (
        f"Expected {ZERO_VIOLATION_FAIL!r}, got {zt_state['decision_basis']!r}."
    )

    # Stop should be early: one safety arm pull (5 probes per zt-001) suffices.
    assert engine.total_queries < 100, (
        f"Engine ran {engine.total_queries} queries. ZERO_VIOLATION_FAIL should fire "
        "within the first safety arm pull (15 probes with probes_per_pull=5)."
    )


# ---------------------------------------------------------------------------
# Test 16: achieved_pass_rate_lower_bound formula and honest certificate fields
# ---------------------------------------------------------------------------

def test_achieved_pass_rate_lower_bound_formula() -> None:
    """achieved_pass_rate_lower_bound is the exact CP lower bound on the true pass rate.

    For a clean run (s == n), the bound is alpha_per_control^(1/n).

    This is the same formula used by STATISTICAL_PASS. When the bound exceeds
    required_pass_rate, the control is decided STATISTICAL_PASS; when it does not,
    the control is decided BUDGET_PASS. Both report the same lower bound field so
    a certificate reader can see the actual statistical strength in either case.

    Key assertions:
    - The bound is None before any probes.
    - The bound is None when some probes fail (s < n).
    - The bound matches alpha^(1/n) exactly on a clean run.
    - The bound tightens as n increases (more probes, stronger bound).
    - When the bound exceeds required_pass_rate, the control is STATISTICAL_PASS.
    - When the bound is below required_pass_rate, the control is BUDGET_PASS.
    """
    import math as _math

    alpha = 0.01
    ctrl = ControlState(
        control_id="test-ctrl",
        suite_id="test-suite",
        is_mandatory=True,
        required_pass_rate=0.90,
    )
    ctrl.alpha_per_control = alpha
    ctrl.n_max = 44   # derived n_max for r=0.90, alpha=0.01

    # Before any probes: None.
    assert ctrl.achieved_pass_rate_lower_bound() is None

    # After partial failure: None.
    ctrl.n = 5
    ctrl.s = 4
    assert ctrl.achieved_pass_rate_lower_bound() is None, (
        "Partial-failure lower bound requires scipy; must return None rather than a wrong value."
    )

    # Clean run at n=20 (below n_max, so BUDGET_PASS territory).
    ctrl.n = 20
    ctrl.s = 20
    expected_at_20 = alpha ** (1.0 / 20)
    bound_at_20 = ctrl.achieved_pass_rate_lower_bound()
    assert bound_at_20 == pytest.approx(expected_at_20, rel=1e-9)
    # At n=20, the bound is below required_pass_rate=0.90 for alpha=0.01.
    assert bound_at_20 < ctrl.required_pass_rate, (
        f"Bound {bound_at_20:.4f} should be below required 0.90 at n=20, alpha=0.01."
    )

    # Clean run at n=44 (the derived n_max, so STATISTICAL_PASS territory).
    ctrl.n = 44
    ctrl.s = 44
    expected_at_44 = alpha ** (1.0 / 44)
    bound_at_44 = ctrl.achieved_pass_rate_lower_bound()
    assert bound_at_44 == pytest.approx(expected_at_44, rel=1e-9)
    # At n_max=44 the bound must exceed required_pass_rate=0.90.
    assert bound_at_44 > ctrl.required_pass_rate, (
        f"Bound {bound_at_44:.4f} should exceed required 0.90 at n=44, alpha=0.01. "
        "This is the condition that defines the derived n_max."
    )

    # Bound tightens monotonically.
    assert bound_at_44 > bound_at_20, (
        "Achieved lower bound must tighten as n increases: more probes, stronger claim."
    )
