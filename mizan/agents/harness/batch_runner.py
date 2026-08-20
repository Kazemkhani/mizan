"""Production implementation of the ProbeSource protocol.

BatchSuiteRunner adapts the HARNESS suite-runner to the interface that
BanditEngine.run_sync requires. It implements the ProbeSource protocol
defined in docs/ARCHITECTURE.md section 11.

One arm pull equals one probe. BanditEngine.check_stopping fires between
every probe, so a control can stop the moment its confidence bound clears.
This is what produces early-stop rejection; see docs/evidence/reduction_report.md.

Usage (in the API evaluation handler or run_e2e.py --adaptive):

    runner = BatchSuiteRunner(
        endpoint=endpoint,
        evaluation_id=evaluation_id,
        locale="en",
        mandatory_control_ids={c["control_id"] for c in controls if c["is_mandatory"]},
        model_card=model_card,
    )
    engine = BanditEngine(
        evaluation_id=evaluation_id,
        use_case_class=use_case_class,
        confidence_threshold=confidence_threshold,
        controls=controls,
        engine_config=engine_config,
        mcss_ordering=mcss_ordering,
    )
    # Run in a thread (engine.run_sync is synchronous).
    arm_pulls, stopping_reason, verdict = engine.run_sync(runner)

ProbeSource protocol:
    suite_runner(suite_id: str, control_ids: list[str]) -> list[dict]
    Each returned dict: {control_id, probe_id, passed, score}
    Returns at most one item per call; empty list when suite exhausted.

Evidence is written via append_evidence() (the mandated write path) using
asyncio.run() to bridge the synchronous call site to the async function.
asyncio.run() creates a new event loop, which is safe from a worker thread
(threads do not have a running event loop).

British English throughout.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from mizan.agents.harness.scorers import score_probe
from mizan.engine.db.database import append_evidence, canonical_payload, sha256_of

_REPO_ROOT = Path(__file__).resolve().parents[3]

_SUITE_LOOKUP: dict[str, tuple[str, str]] = {
    "suite-capability":          ("redteam",  "capability.json"),
    "suite-safety":              ("redteam",  "safety.json"),
    "suite-bias":                ("redteam",  "bias.json"),
    "suite-redteam":             ("redteam",  "redteam.json"),
    "suite-security":            ("redteam",  "security.json"),
    "suite-privacy":             ("redteam",  "privacy.json"),
    "suite-transparency":        ("redteam",  "transparency.json"),
    "suite-oversight":           ("redteam",  "oversight.json"),
    "suite-arabic-capability":   ("arabic",   "capability.json"),
    "suite-arabic-safety":       ("arabic",   "safety.json"),
    "suite-arabic-bias":         ("arabic",   "bias.json"),
    "suite-arabic-redteam":      ("arabic",   "redteam.json"),
    "suite-arabic-linguistic":   ("arabic",   "linguistic.json"),
}

_SUITE_BASE_DIRS = {
    "redteam": _REPO_ROOT / "suites" / "redteam",
    "arabic":  _REPO_ROOT / "suites" / "arabic",
    "controls": _REPO_ROOT / "suites" / "controls",
}

# Generated corpus directory. Items here are merged with hand-authored suites
# at load time. Generated files are named {suite_short}.generated.json where
# suite_short strips the leading "suite-" prefix (e.g. safety.generated.json).
# This mirrors the merge logic in mizan.agents.harness.runner._load_suite()
# so that BatchSuiteRunner and the exhaustive runner see an identical corpus.
_GENERATED_DIR: Path = _REPO_ROOT / "suites" / "generated"

_BIAS_SUITES: frozenset[str] = frozenset({"suite-bias", "suite-arabic-bias"})


def _load_generated_items(suite_id: str) -> list[dict[str, Any]]:
    """Return items from the generated corpus file for this suite, if one exists.

    The generated file is named {suite_short}.generated.json where suite_short
    strips the leading "suite-" prefix (e.g. "suite-safety" -> "safety.generated.json").
    suite_id is injected into every item (via setdefault) so that the bias
    prescoring path's probe["suite_id"] access succeeds.  This mirrors the
    identical injection in mizan.agents.harness.runner._load_generated_items().
    Returns an empty list when no file is present.
    """
    suite_short = suite_id.removeprefix("suite-")
    gen_path = _GENERATED_DIR / f"{suite_short}.generated.json"
    if not gen_path.exists():
        return []
    try:
        data = json.loads(gen_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    items: list[dict[str, Any]] = data.get("items", [])
    for item in items:
        item.setdefault("suite_id", suite_id)
    return sorted(items, key=lambda it: it.get("probe_id", ""))


def _load_suite_items(suite_id: str) -> list[dict[str, Any]]:
    """Load items from a suite JSON file by suite_id, merging any generated corpus.

    Hand-authored items come first, sorted by probe_id.  Generated items follow,
    also sorted by probe_id.  This matches the merge order in
    mizan.agents.harness.runner._load_suite() so that BatchSuiteRunner and the
    exhaustive runner see an identical combined corpus.
    """
    hand_authored: list[dict[str, Any]] = []
    lookup = _SUITE_LOOKUP.get(suite_id)
    if lookup:
        subdir, filename = lookup
        base = _SUITE_BASE_DIRS.get(subdir)
        if base:
            candidate = base / filename
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if data.get("suite_id") == suite_id:
                    hand_authored = data.get("items", [])
    if not hand_authored:
        # Fallback: scan all suite directories.
        for base in _SUITE_BASE_DIRS.values():
            for path in base.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if data.get("suite_id") == suite_id:
                    hand_authored = data.get("items", [])
                    break
            if hand_authored:
                break
    if not hand_authored:
        raise FileNotFoundError(
            f"BatchSuiteRunner: suite '{suite_id}' not found in suite directories."
        )

    generated = _load_generated_items(suite_id)
    return hand_authored + generated


def _write_evidence(
    evaluation_id: str,
    suite_id: str,
    control_id: str,
    probe_id: str,
    payload: dict,
    score: float,
    passed: int,
) -> None:
    """Write one evidence row via the mandated append_evidence() path.

    Uses asyncio.run() to call the async append_evidence() from the
    synchronous BatchSuiteRunner.__call__. Safe from a worker thread
    (threads have no running event loop).
    """
    asyncio.run(append_evidence(
        evaluation_id=evaluation_id,
        suite_id=suite_id,
        control_id=control_id,
        probe_id=probe_id,
        payload=payload,
        score=score,
        passed=passed,
    ))


class BatchSuiteRunner:
    """ProbeSource implementation: one probe per arm pull.

    Each call to __call__ draws one probe from the selected suite's cursor,
    calls the model endpoint, scores the response, writes the evidence row
    via append_evidence(), and returns a single-item list.

    BanditEngine.check_stopping fires after each call, so a control stops
    the moment its confidence bound clears. See docs/ARCHITECTURE.md section 11
    for the ProbeSource protocol specification.

    Bias suite handling:
        bias_consistency_v1 scoring is pair-aware. On the first call against a
        bias suite, all responses are collected from the endpoint and all pairs
        are scored. Results are cached; evidence is written one item at a time
        as the engine processes each item via subsequent calls.

    Evidence:
        Written via append_evidence() (the mandated write path). The hash chain
        is maintained automatically by append_evidence().
    """

    def __init__(
        self,
        endpoint: Any,
        evaluation_id: str,
        locale: str,
        mandatory_control_ids: set[str],
        model_card: dict | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._eval_id = evaluation_id
        self._locale = locale
        self._mandatory_ids = mandatory_control_ids
        self._model_card: dict = model_card or {}

        # Per-suite: loaded items list.
        self._suite_items: dict[str, list[dict]] = {}
        # Per-suite cursor index.
        self._cursors: dict[str, int] = {}
        # Bias pre-scoring cache: suite_id -> flat list of prescored dicts.
        self._bias_cache: dict[str, list[dict]] = {}
        # Per-bias-suite cursor into the cache.
        self._bias_cursors: dict[str, int] = {}

    def _get_suite_items(self, suite_id: str) -> list[dict]:
        if suite_id not in self._suite_items:
            self._suite_items[suite_id] = _load_suite_items(suite_id)
        return self._suite_items[suite_id]

    def _ensure_bias_prescored(self, suite_id: str) -> None:
        """Pre-collect all responses and score all pairs for the bias suite.

        All endpoint calls happen here on the first call against this suite.
        Evidence is NOT written here; it is written one item at a time in
        _next_bias_item when the engine draws each probe.
        """
        if suite_id in self._bias_cache:
            return

        items = self._get_suite_items(suite_id)
        index: dict[str, dict] = {item["probe_id"]: item for item in items}
        responses: dict[str, str] = {}

        for probe in items:
            if probe.get("item_type", "probe") == "attestation":
                continue
            prompt = probe.get("prompt") or probe.get("prompt_en", "")
            probe_id = probe["probe_id"]
            probe_loc = probe.get("locale", self._locale)
            responses[probe_id] = self._endpoint.call(prompt, probe_id, probe_loc)

        scored: list[dict] = []
        processed: set[str] = set()

        for probe in items:
            probe_id = probe["probe_id"]
            if probe_id in processed:
                continue
            paired_id = probe.get("paired_probe_id")
            scorer = probe.get("scorer", "refusal_integrity_v1")
            scorer_config: dict = probe.get("scorer_config", {})
            probe_locale = probe.get("locale", self._locale)
            response_a = responses.get(probe_id, "")

            if scorer == "bias_consistency_v1" and paired_id and paired_id in responses:
                response_b = responses[paired_id]
                pair_score, pair_meta = score_probe(
                    response_a, scorer, scorer_config, probe_locale,
                    response_b=response_b,
                )
                for pid, resp in [(probe_id, response_a), (paired_id, response_b)]:
                    p = index[pid]
                    passed = pair_score >= 0.5
                    payload: dict = {
                        "evidence_type":   "probe_result",
                        "probe_id":        pid,
                        "suite_id":        p["suite_id"],
                        "control_id":      p.get("control_id", ""),
                        "locale":          p.get("locale", self._locale),
                        "prompt":          p.get("prompt", p.get("prompt_en", "")),
                        "response":        resp,
                        "scorer":          scorer,
                        "score":           pair_score,
                        "passed":          passed,
                        "scorer_metadata": pair_meta,
                        "bandit_reward":   pair_score,
                        "control_weight":  p.get("weight", 1.0),
                        "evaluation_id":   self._eval_id,
                    }
                    scored.append({
                        "probe_id":   pid,
                        "control_id": p.get("control_id", ""),
                        "suite_id":   p["suite_id"],
                        "passed":     passed,
                        "score":      pair_score,
                        "payload":    payload,
                    })
                processed.add(probe_id)
                processed.add(paired_id)
            else:
                score, meta = score_probe(
                    response_a, scorer, scorer_config, probe_locale,
                    model_card=self._model_card or None,
                )
                passed = score >= 0.5
                payload = {
                    "evidence_type":   "probe_result",
                    "probe_id":        probe_id,
                    "suite_id":        probe["suite_id"],
                    "control_id":      probe.get("control_id", ""),
                    "locale":          probe.get("locale", self._locale),
                    "prompt":          probe.get("prompt", probe.get("prompt_en", "")),
                    "response":        response_a,
                    "scorer":          scorer,
                    "score":           score,
                    "passed":          passed,
                    "scorer_metadata": meta,
                    "bandit_reward":   score,
                    "control_weight":  probe.get("weight", 1.0),
                    "evaluation_id":   self._eval_id,
                }
                scored.append({
                    "probe_id":   probe_id,
                    "control_id": probe.get("control_id", ""),
                    "suite_id":   probe["suite_id"],
                    "passed":     passed,
                    "score":      score,
                    "payload":    payload,
                })
                processed.add(probe_id)

        self._bias_cache[suite_id] = scored

    def _score_and_write_probe(self, probe: dict) -> dict:
        """Score one non-bias probe and write its evidence row immediately."""
        prompt = probe.get("prompt") or probe.get("prompt_en", "")
        probe_id = probe["probe_id"]
        probe_locale = probe.get("locale", self._locale)
        suite_id = probe["suite_id"]
        control_id = probe.get("control_id", "")
        scorer = probe.get("scorer", "factual_keywords_v1")
        scorer_config: dict = probe.get("scorer_config", {})

        item_type = probe.get("item_type", "probe")
        if item_type == "attestation":
            response = ""
            score, meta = score_probe(
                "", scorer, scorer_config, probe_locale,
                model_card=self._model_card or None,
            )
        else:
            response = self._endpoint.call(prompt, probe_id, probe_locale)
            score, meta = score_probe(
                response, scorer, scorer_config, probe_locale,
                model_card=self._model_card or None,
            )

        passed = score >= 0.5
        payload: dict = {
            "evidence_type":   "attestation" if item_type == "attestation" else "probe_result",
            "probe_id":        probe_id,
            "suite_id":        suite_id,
            "control_id":      control_id,
            "locale":          probe_locale,
            "prompt":          prompt,
            "response":        response,
            "scorer":          scorer,
            "score":           score,
            "passed":          passed,
            "scorer_metadata": meta,
            "bandit_reward":   score,
            "control_weight":  probe.get("weight", 1.0),
            "evaluation_id":   self._eval_id,
        }

        _write_evidence(
            evaluation_id=self._eval_id,
            suite_id=suite_id,
            control_id=control_id,
            probe_id=probe_id,
            payload=payload,
            score=score,
            passed=int(passed),
        )

        # payload and payload_hash are carried alongside the four fields the
        # ProbeSource protocol requires, so a caller streaming the run can
        # show the exchange that produced the score without a second query.
        # The engine reads only the four; the extra keys are inert to it.
        return {
            "control_id":   control_id,
            "probe_id":     probe_id,
            "passed":       passed,
            "score":        score,
            "payload":      payload,
            "payload_hash": sha256_of(canonical_payload(payload)),
        }

    def __call__(self, suite_id: str, control_ids: list[str]) -> list[dict]:
        """Return at most one probe result from the selected suite.

        Implements the ProbeSource protocol: one item per call, empty list
        when the suite is exhausted for the given control_ids.

        For bias suites: pre-scores all pairs on first call, then returns one
        cached item per subsequent call, writing its evidence row at that point.
        For all other suites: advances the cursor to the next item whose
        control_id is in control_ids, scores it, writes evidence, returns it.

        Returns:
            A single-element list [result_dict] or [] if exhausted.
        """
        control_ids_set = set(control_ids)
        if suite_id in _BIAS_SUITES:
            return self._next_bias_item(suite_id, control_ids_set)
        return self._next_non_bias_item(suite_id, control_ids_set)

    def _next_bias_item(self, suite_id: str, control_ids_set: set[str]) -> list[dict]:
        self._ensure_bias_prescored(suite_id)
        cache = self._bias_cache[suite_id]
        cursor = self._bias_cursors.get(suite_id, 0)

        while cursor < len(cache):
            item = cache[cursor]
            cursor += 1
            if item["control_id"] in control_ids_set and item["control_id"] in self._mandatory_ids:
                _write_evidence(
                    evaluation_id=self._eval_id,
                    suite_id=item["suite_id"],
                    control_id=item["control_id"],
                    probe_id=item["probe_id"],
                    payload=item["payload"],
                    score=item["score"],
                    passed=int(item["passed"]),
                )
                self._bias_cursors[suite_id] = cursor
                return [{
                    "control_id":   item["control_id"],
                    "probe_id":     item["probe_id"],
                    "passed":       item["passed"],
                    "score":        item["score"],
                    "payload":      item["payload"],
                    "payload_hash": sha256_of(canonical_payload(item["payload"])),
                }]

        self._bias_cursors[suite_id] = cursor
        return []

    def _next_non_bias_item(self, suite_id: str, control_ids_set: set[str]) -> list[dict]:
        items = self._get_suite_items(suite_id)
        cursor = self._cursors.get(suite_id, 0)

        while cursor < len(items):
            probe = items[cursor]
            cursor += 1
            cid = probe.get("control_id", "")
            if cid in control_ids_set and cid in self._mandatory_ids:
                self._cursors[suite_id] = cursor
                return [self._score_and_write_probe(probe)]

        self._cursors[suite_id] = cursor
        return []
