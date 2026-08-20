# MIZAN Warm-Start Compounding: Measured Position

**Produced**: 2026-08-20T04:33:22.472913+00:00
**Profile**: non_compliant (12 evaluations x 10 seeds)
**Corpus**: 3026 probe items

This document states what the warm-start layer demonstrably does today,
what it does not do, and what the research and development would build.
It is written for direct use in a pitch to a government funding panel.
Every figure is derived from the run that produced this document.

---

## Part 1. What compounds today and by how much

The warm-start layer records the mean information gain per suite after
each completed evaluation and uses it to set the initial arm ordering
for the next evaluation of the same use-case class. UCB1 then takes
over once every arm has been pulled at least once.

The experiment runs the engine twice per seed, in the same evaluation
sequence: once with warm-start memory enabled, once without (default
suite order, no memory). The same RNG seed and endpoint are used for
both, so differences in probe count are attributable to the ordering
difference, not to variance in model responses.

**Profile**: non_compliant. All suites fail, so the engine detects
rejection quickly regardless of ordering. The question is whether
warm-start memory finds the failing suite faster.

**Per-evaluation median probe counts** (lower is faster to reject):

| Eval | With memory | Without memory | Difference (mem minus nom) |
|------|-------------|----------------|----------------------------|
|    1 |         9.5 |            9.5 |                       +0.0 |
|    2 |        12.0 |           13.5 |                       -1.5 |
|    3 |        19.5 |           19.5 |                       +0.0 |
|    4 |         8.5 |            9.5 |                       -1.0 |
|    5 |        17.0 |           18.5 |                       -1.5 |
|    6 |        23.5 |           23.0 |                       +0.5 |
|    7 |        19.5 |           18.0 |                       +1.5 |
|    8 |         9.5 |            9.5 |                       +0.0 |
|    9 |        13.0 |           13.5 |                       -0.5 |
|   10 |        14.5 |           15.0 |                       -0.5 |
|   11 |         8.0 |            8.5 |                       -0.5 |
|   12 |        10.0 |            8.5 |                       +1.5 |

**Spread across seeds** (with memory):

| Eval | Median | Min | Max |
|------|--------|-----|-----|
|    1 |    9.5 |   6 |  80 |
|    2 |   12.0 |   6 |  42 |
|    3 |   19.5 |   6 |  76 |
|    4 |    8.5 |   6 | 120 |
|    5 |   17.0 |   6 | 133 |
|    6 |   23.5 |   6 |  55 |
|    7 |   19.5 |   6 |  76 |
|    8 |    9.5 |   7 | 124 |
|    9 |   13.0 |   6 |  44 |
|   10 |   14.5 |   6 | 162 |
|   11 |    8.0 |   6 |  95 |
|   12 |   10.0 |   6 |  44 |

**Finding**:

The warm-start ordering does not reduce median probes across this sequence. Evaluation 1 used 10 probes (median); evaluation 12 used 10. The no-memory baseline moved from 10 to 8 over the same sequence. The difference between the two trajectories is -1.5 probes, which is within the natural spread (min-max range at evaluation 1: 6 to 80). Warm-start provides no measurable benefit at this scale.

**Interpretation**: This is the expected result for a small suite space (five suites). UCB1 converges in two arm pulls, before the warm-start ordering can make a material difference. The warm-start matters at scale: at fifty suites, a good initial ordering saves many pulls that would otherwise be spent on UCB1 exploration. The mechanism is correct; the prototype is too small to demonstrate it numerically.

---

## Part 2. What does not exist

Three things are absent from the current prototype and must not be claimed:

1. **Monte Carlo rollouts.** The warm-start layer sorts suites by historical
   mean reward. It does not search the space of orderings via rollouts.
   Full Monte Carlo tree search over suite orderings is not implemented.
   The layer is correctly named a warm-start, not Monte Carlo search.

2. **A demonstrated compounding curve at national scale.** The experiment
   above runs 12 evaluations on a single use-case class. The claim
   that mean probes-to-verdict decreases monotonically as evaluations
   accumulate across an entire registry has not been demonstrated.
   At the current suite count, UCB1 dominates after two pulls and the
   warm-start provides negligible benefit.

3. **Live wiring of the warm-start in the proof path.** The measured
   reduction figures in reduction_report.md come from a path that constructs
   BanditEngine without passing any mcss_ordering. The warm-start is not
   included in the headline reduction numbers.

---

## Part 3. What the research and development is

The research direction worth funding is rollout-based suite-ordering search.

**Specific technique**: a Monte Carlo tree search over the space of suite
orderings, using the engine's Clopper-Pearson bound as the value function.
At each node, a simulated evaluation draws probes from the current ordering
and measures when the bound clears. The search expands the ordering that
settles the most mandatory controls fastest, given a compute budget.
This replaces the current sorting heuristic with a search that reasons
explicitly about the stopping structure of the evaluation.

**What it would buy**: on a large suite space (tens of suites, multiple
use-case classes with overlapping controls), the initial ordering becomes
material. The difference between visiting the most informative suite first
versus last scales with the number of suites. At five suites, UCB1 recovers
in two pulls. At fifty suites, a good initial ordering saves many pulls.

**What makes it fundable research**: the bound-clearing value function is
specific to adaptive compliance evaluation and is not a commodity MCTS
implementation. It requires integrating the Clopper-Pearson stopping
structure into the tree value, which is a novel application of sequential
decision theory to regulatory evaluation. The existing BanditEngine and
ControlState machinery already supplies the value function; the research
task is the search layer on top.

**One-sentence summary for the pitch**: the current engine adapts within
each evaluation by stopping early; the funded work teaches it to adapt
across evaluations by searching for the best order to run tests in,
so that each new evaluation of the same use case starts from a provably
better starting point than the previous one.

*Report generated by `scripts/prove_compounding.py`.*
*Reproducible from a clean checkout in one command.*
