"""Inter-evaluation suite-ordering warm-start layer.

STATUS: dormant. The proof path (prove_reduction.py) constructs BanditEngine
directly and does not wire the MCSS warm-start. The production path
(run_e2e.py) and the API route run suites exhaustively and do not use the
engine at all. This layer is not exercised by any current evaluation path.
It is retained because the mechanism is sound and the wiring task is well-
defined; see docs/FLOW.md for the integration plan.

NAMING NOTE
===========
This module was initially named "Monte Carlo Strategy Search". That name
implies rollout-based search over orderings, which this module does not do.
The mechanism is a simpler inter-evaluation warm-start: historical mean
rewards per suite are recorded after each evaluation and used to set the
initial arm ordering for the next evaluation of the same use-case class.
UCB1 then takes over once every arm has been pulled at least once. This is
more accurately described as a reward-sorted warm-start.

WHAT IS BEING LEARNT
====================
The layer learns the best *initial arm ordering* for each use-case class:
which suite should be pulled first, second, and so on, to maximise expected
information gain per query. This is the state the engine enters each
evaluation with before UCB1 takes over.

State space: a partial ordering over the arms (suites) for a given
use-case class. The state that matters for learning is which suite was
pulled in which position, and what mean reward it yielded in that position.

Learning mechanism: after each completed evaluation, the layer updates a
statistics table that maps (use_case_class, suite_id) to the historical mean
information-gain-per-query for that suite in evaluations of this class. The
next evaluation starts with arms ordered by this historical mean, descending.
UCB1 then overrides this ordering once it has enough observations to improve
on the warm-start.

COMPOUNDING CLAIM
=================
Evaluation N+1 of the same use-case class starts with a better arm ordering
than evaluation N, until the ordering converges. Convergence is detectable:
once the warm-start ordering matches the UCB1 exploitation order from the
most recent evaluation, no further improvement is possible from ordering alone.

The improvement is measurable as: average probes-to-verdict for evaluations
of the same class decreases as total_evaluations increases, when plotted
against a random-ordering baseline.

WHAT THIS LAYER DOES NOT DO
============================
This layer does not search the exponential space of all orderings via
rollouts. That would be a full Monte Carlo tree search and is not implemented
here. The arm space is small (eight suites at most), the evaluation budget is
finite, and UCB1 already handles the exploitation-exploration trade-off within
each evaluation. This layer adds only inter-evaluation learning of a good
warm-start, not a within-evaluation search over orderings.

PERSISTENCE
===========
MCSS state is stored in the engine_memory table, keyed by use_case_class.
Each row holds:
  suite_ordering: JSON list of suite_ids in learnt descending order.
  arm_statistics: JSON object mapping suite_id to {mean_reward, pulls}.
  total_evaluations: count of completed evaluations contributing to this row.

The MIZAN DB layer (database.py) provides the session factory. MCSSLayer
wraps the raw SQLAlchemy calls.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from mizan.api.schemas import ArmPull
from mizan.engine.db.database import get_session


class MCSSLayer:
    """Inter-evaluation learning of optimal suite orderings.

    Usage pattern for one evaluation:

        layer = await MCSSLayer.load(use_case_class, suite_ids, session)
        ordering = layer.get_suite_ordering()           # warm-start UCB1
        # ... run BanditEngine with this ordering ...
        layer.update(arm_pulls)                         # absorb results
        await layer.save(session)                       # persist to DB
    """

    def __init__(
        self,
        use_case_class: str,
        suite_ids: list[str],
        arm_statistics: dict[str, dict],
        total_evaluations: int,
    ) -> None:
        self._use_case_class = use_case_class
        self._suite_ids = list(suite_ids)
        # arm_statistics: {suite_id: {mean_reward: float, pulls: int}}
        self._arm_statistics: dict[str, dict] = arm_statistics
        self._total_evaluations: int = total_evaluations

    # ---------------------------------------------------------------------------
    # Construction
    # ---------------------------------------------------------------------------

    @classmethod
    def _from_row(
        cls,
        use_case_class: str,
        suite_ids: list[str],
        row: dict,
    ) -> "MCSSLayer":
        """Construct from a raw engine_memory row dict."""
        raw_stats = row.get("arm_statistics") or {}
        if isinstance(raw_stats, str):
            raw_stats = json.loads(raw_stats)
        return cls(
            use_case_class=use_case_class,
            suite_ids=suite_ids,
            arm_statistics=raw_stats,
            total_evaluations=int(row.get("total_evaluations") or 0),
        )

    @classmethod
    def fresh(cls, use_case_class: str, suite_ids: list[str]) -> "MCSSLayer":
        """Return a fresh MCSS layer with no historical data.

        Used when no engine_memory row exists for this use_case_class.
        The initial suite ordering is the order of suite_ids as supplied
        (typically the declaration order in use_cases.json).
        """
        return cls(
            use_case_class=use_case_class,
            suite_ids=suite_ids,
            arm_statistics={},
            total_evaluations=0,
        )

    @classmethod
    async def load(
        cls,
        use_case_class: str,
        suite_ids: list[str],
        session: AsyncSession,
    ) -> "MCSSLayer":
        """Load MCSS state from engine_memory, or return fresh state if absent.

        Args:
            use_case_class: Matches engine_memory.use_case_class.
            suite_ids:      All suite IDs for this use case (mandatory and advisory).
            session:        Live SQLAlchemy async session (caller manages lifetime).
        """
        result = await session.execute(
            text(
                "SELECT arm_statistics, total_evaluations "
                "FROM engine_memory WHERE use_case_class = :cls"
            ),
            {"cls": use_case_class},
        )
        row = result.mappings().first()
        if row is None:
            return cls.fresh(use_case_class, suite_ids)
        return cls._from_row(use_case_class, suite_ids, dict(row))

    # ---------------------------------------------------------------------------
    # Ordering
    # ---------------------------------------------------------------------------

    def get_suite_ordering(self) -> list[str]:
        """Return suite IDs in learnt descending order of expected information yield.

        Suites with higher historical mean reward per query come first. Suites
        with no historical data are appended at the end in their original order.
        This is the warm-start passed to BanditEngine as mcss_ordering.
        """
        known = sorted(
            [s for s in self._suite_ids if s in self._arm_statistics],
            key=lambda s: self._arm_statistics[s].get("mean_reward", 0.0),
            reverse=True,
        )
        unknown = [s for s in self._suite_ids if s not in self._arm_statistics]
        return known + unknown

    # ---------------------------------------------------------------------------
    # Update after evaluation
    # ---------------------------------------------------------------------------

    def update(self, arm_pulls: list[ArmPull]) -> None:
        """Absorb arm-pull results from a completed evaluation.

        Updates the running mean reward per suite using a cumulative mean
        formula: new_mean = (old_mean * old_pulls + new_total_reward) / (old_pulls + new_pulls).

        This is an online update: no historical data is lost when new results
        arrive. The mean converges as total_evaluations grows.
        """
        for pull in arm_pulls:
            suite_id = pull.suite_id
            if suite_id not in self._arm_statistics:
                self._arm_statistics[suite_id] = {"mean_reward": 0.0, "pulls": 0}
            stats = self._arm_statistics[suite_id]
            old_pulls = stats["pulls"]
            old_mean = stats["mean_reward"]
            # Update running mean.
            new_pulls = old_pulls + 1
            new_mean = (old_mean * old_pulls + pull.reward) / new_pulls
            stats["pulls"] = new_pulls
            stats["mean_reward"] = round(new_mean, 8)

        self._total_evaluations += 1

    # ---------------------------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------------------------

    async def save(self, session: AsyncSession) -> None:
        """Upsert the MCSS state into engine_memory.

        Uses INSERT OR REPLACE (SQLite) which atomically replaces an existing
        row for the same use_case_class. The suite_ordering column is kept as
        a convenience for human inspection of the DB; the authoritative ordering
        is always recomputed from arm_statistics at load time.

        SOVEREIGN-TODO (Wave 3): replace INSERT OR REPLACE with ON CONFLICT DO UPDATE
        for Postgres compatibility.
        """
        ordering = self.get_suite_ordering()
        now = datetime.now(timezone.utc).isoformat()
        await session.execute(
            text(
                """
                INSERT OR REPLACE INTO engine_memory
                    (use_case_class, suite_ordering, arm_statistics, total_evaluations, updated_at)
                VALUES
                    (:cls, :ordering, :stats, :total_evals, :now)
                """
            ),
            {
                "cls": self._use_case_class,
                "ordering": json.dumps(ordering),
                "stats": json.dumps(self._arm_statistics),
                "total_evals": self._total_evaluations,
                "now": now,
            },
        )

    # ---------------------------------------------------------------------------
    # Introspection
    # ---------------------------------------------------------------------------

    @property
    def total_evaluations(self) -> int:
        """Number of completed evaluations that have contributed to this memory."""
        return self._total_evaluations

    @property
    def arm_statistics(self) -> dict[str, dict]:
        """Read-only view of per-suite statistics."""
        return dict(self._arm_statistics)

    def convergence_delta(self, previous_ordering: list[str]) -> float:
        """Measure how much the ordering changed from a prior state.

        Returns the normalised Kendall tau distance between previous_ordering
        and the current ordering, in [0, 1]. A value of 0.0 means the ordering
        has not changed (converged). A value of 1.0 means the ordering is
        completely reversed.

        Used by Wave 2 prove_reduction.py to plot ordering improvement over time.
        """
        current = self.get_suite_ordering()
        n = len(current)
        if n <= 1:
            return 0.0

        # Map each suite to its rank in previous and current orderings.
        prev_rank = {s: i for i, s in enumerate(previous_ordering)}
        curr_rank = {s: i for i, s in enumerate(current)}

        # Count discordant pairs (different relative order in the two orderings).
        discordant = 0
        pairs = 0
        for i in range(n):
            for j in range(i + 1, n):
                si, sj = current[i], current[j]
                if si in prev_rank and sj in prev_rank:
                    pairs += 1
                    if (curr_rank[si] < curr_rank[sj]) != (prev_rank[si] < prev_rank[sj]):
                        discordant += 1

        if pairs == 0:
            return 0.0
        return discordant / pairs

    # ---------------------------------------------------------------------------
    # Synchronous loader (for tests that run without an event loop)
    # ---------------------------------------------------------------------------

    @classmethod
    def load_sync(
        cls,
        use_case_class: str,
        suite_ids: list[str],
        db_path: str,
    ) -> "MCSSLayer":
        """Load MCSS state synchronously from SQLite. Test-only path.

        SOVEREIGN-TODO: not for production use. Production always goes through
        the async path (load()) which handles both SQLite and Postgres.
        """
        import sqlite3
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT arm_statistics, total_evaluations "
                "FROM engine_memory WHERE use_case_class = ?",
                (use_case_class,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return cls.fresh(use_case_class, suite_ids)

        raw_stats = row[0]
        if isinstance(raw_stats, str):
            raw_stats = json.loads(raw_stats)
        return cls(
            use_case_class=use_case_class,
            suite_ids=suite_ids,
            arm_statistics=raw_stats or {},
            total_evaluations=int(row[1] or 0),
        )

    def save_sync(self, db_path: str) -> None:
        """Persist MCSS state synchronously to SQLite. Test-only path."""
        import sqlite3
        ordering = self.get_suite_ordering()
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO engine_memory
                    (use_case_class, suite_ordering, arm_statistics, total_evaluations, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self._use_case_class,
                    json.dumps(ordering),
                    json.dumps(self._arm_statistics),
                    self._total_evaluations,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()
