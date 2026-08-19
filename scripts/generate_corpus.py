"""
Deterministic corpus generator for MIZAN Wave 1.

Slot selection: SHA-256(grammar_id:control_id:group_id:template_idx:slot_name:item_seq:seed)
  -> int.from_bytes(digest[:4], "big") % len(slot_values)

Every generated item records full provenance.
Exact-duplicate detection enforced (fails on collision).
Near-duplicate count reported (edit distance <= 20).
Output: suites/generated/{suite_id}.generated.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
GRAMMARS_DIR = REPO_ROOT / "suites" / "grammars"
OUTPUT_DIR = REPO_ROOT / "suites" / "generated"

# Grammars whose controls are not probe-type (attestation only) -- skip.
ATTESTATION_ONLY_CONTROLS = {"ctrl-hov-001"}


def _sha256_slot(key: str, slot_values: list[str]) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    idx = int.from_bytes(digest[:4], "big") % len(slot_values)
    return slot_values[idx]


def _fill_template(
    template: str,
    slots: dict[str, list[str]],
    grammar_id: str,
    control_id: str,
    group_id: str,
    template_idx: int,
    item_seq: int,
    seed: int,
) -> tuple[str, dict[str, str]]:
    """Fill one template deterministically; return (filled_text, filled_slots_map)."""
    import re

    slot_names = re.findall(r"\{(\w+)\}", template)
    filled: dict[str, str] = {}
    for slot_name in slot_names:
        if slot_name not in slots:
            continue
        key = f"{grammar_id}:{control_id}:{group_id}:{template_idx}:{slot_name}:{item_seq}:{seed}"
        filled[slot_name] = _sha256_slot(key, slots[slot_name])
    result = template
    for slot_name, value in filled.items():
        result = result.replace("{" + slot_name + "}", value)
    return result, filled


def _normalise(text: str) -> str:
    """Normalise for duplicate detection."""
    import unicodedata
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.lower().split())


def _edit_distance(a: str, b: str, cap: int = 21) -> int:
    """Levenshtein distance, capped at cap for speed."""
    if abs(len(a) - len(b)) >= cap:
        return cap
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1] + [0] * len(b)
        for j, cb in enumerate(b):
            curr[j + 1] = min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if ca == cb else 1),
            )
            if curr[j + 1] >= cap:
                curr[j + 1] = cap
        prev = curr
    return prev[len(b)]


def _probe_id(grammar_id: str, control_id: str, group_id: str, seq: int) -> str:
    short_grammar = grammar_id.replace("-v1", "").replace("-", "")
    short_group = group_id.replace(control_id + "-", "").replace("-", "")[:12]
    return f"gen-{short_grammar}-{short_group}-{seq:04d}"


def _generate_control(
    grammar: dict[str, Any],
    control_id: str,
    control_def: dict[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    """Generate all items for one control from its template_groups."""
    grammar_id = grammar["grammar_id"]
    n_target = control_def["n_target"]
    scorer = control_def["scorer"]
    scorer_config = control_def.get("scorer_config", {})
    locale_split = control_def.get("locale_split", {"en": 1.0})

    groups = control_def.get("template_groups", [])
    if not groups:
        log.warning("Control %s has no template_groups -- skipping.", control_id)
        return []

    # Per-locale quota: ensure locale distribution matches locale_split.
    # Each locale gets a pool of up to n_target * ratio * 3 items; after all
    # groups are processed, each pool is trimmed to n_target * ratio.
    locale_pool: dict[str, list[dict[str, Any]]] = defaultdict(list)
    locale_seen: dict[str, set[str]] = defaultdict(set)
    near_dup_count = 0
    seq = 0

    # Per-locale cap during generation (3x to allow dedup headroom)
    locale_caps: dict[str, int] = {
        loc: max(1, round(n_target * ratio * 3))
        for loc, ratio in locale_split.items()
    }

    for group in groups:
        group_id: str = group["group_id"]
        locale: str = group.get("locale", "en")
        slots: dict[str, list[str]] = group.get("slots", {})

        templates_en: list[str] = group.get("templates_en", [])
        templates_ar: list[str] = group.get("templates_ar", [])
        templates_en_b: list[str] = group.get("templates_en_b", [])
        templates_ar_b: list[str] = group.get("templates_ar_b", [])

        primary_templates = templates_ar if locale == "ar" else templates_en
        b_templates = templates_ar_b if locale == "ar" else templates_en_b
        is_paired = bool(b_templates)

        if not primary_templates:
            log.warning("Group %s/%s has no templates -- skipping.", control_id, group_id)
            continue

        # Check if this locale's pool is already full.
        locale_cap = locale_caps.get(locale, n_target * 3)
        if len(locale_pool[locale]) >= locale_cap:
            log.debug("Group %s/%s: locale %s pool full, skipping.", control_id, group_id, locale)
            continue

        n_groups_for_locale = sum(
            1 for g in groups if g.get("locale", "en") == locale
        )
        group_target = max(1, (locale_cap * 2) // max(1, n_groups_for_locale))

        slot_combinations: list[dict[str, str]] = []
        slot_keys = list(slots.keys())
        if slot_keys:
            slot_value_lists = [slots[k] for k in slot_keys]
            all_combinations = list(product(*slot_value_lists))
            max_combos = min(len(all_combinations), group_target * 4)
            all_combinations = all_combinations[:max_combos]
            for combo in all_combinations:
                slot_combinations.append(dict(zip(slot_keys, combo)))
        else:
            slot_combinations = [{}]

        seen = locale_seen[locale]

        for t_idx, template in enumerate(primary_templates):
            for combo_idx, combo in enumerate(slot_combinations):
                if len(locale_pool[locale]) >= locale_cap:
                    break

                filled_text = template
                filled_b_text: str | None = None
                provenance_slots: dict[str, str] = {}

                for slot_name, slot_value in combo.items():
                    filled_text = filled_text.replace("{" + slot_name + "}", slot_value)
                    provenance_slots[slot_name] = slot_value

                if is_paired and b_templates:
                    b_template = b_templates[t_idx % len(b_templates)]
                    b_slots = {k: v for k, v in combo.items()}
                    for slot_name in list(b_slots.keys()):
                        b_slot_key = slot_name + "_b"
                        if b_slot_key in slots:
                            key = f"{grammar_id}:{control_id}:{group_id}:{t_idx}:{b_slot_key}:{combo_idx}:{seed}"
                            b_slots[b_slot_key.replace("_b", "")] = _sha256_slot(key, slots[b_slot_key])
                    filled_b_text = b_template
                    for sn, sv in b_slots.items():
                        filled_b_text = filled_b_text.replace("{" + sn + "}", sv)
                    import re as _re
                    filled_b_text = _re.sub(r"\{[^}]+\}", "[SLOT]", filled_b_text)

                import re as _re
                filled_text = _re.sub(r"\{[^}]+\}", "[SLOT]", filled_text)

                norm = _normalise(filled_text)
                if norm in seen:
                    log.debug("Exact duplicate skipped in %s/%s.", control_id, group_id)
                    continue

                for existing_norm in list(seen)[-200:]:
                    if _edit_distance(norm, existing_norm) <= 20:
                        near_dup_count += 1
                        break

                seen.add(norm)
                probe_id_str = _probe_id(grammar_id, control_id, group_id, seq)
                seq += 1

                item: dict[str, Any] = {
                    "probe_id": probe_id_str,
                    "control_id": control_id,
                    "locale": locale,
                    "prompt": filled_text,
                    "scorer": scorer,
                    "scorer_config": scorer_config,
                    "provenance": {
                        "source": "generated",
                        "grammar_id": grammar_id,
                        "group_id": group_id,
                        "template_idx": t_idx,
                        "slots_filled": provenance_slots,
                        "seed": seed,
                    },
                }

                if is_paired and filled_b_text:
                    b_norm = _normalise(filled_b_text)
                    # Skip the whole pair if the b-text would be a duplicate.
                    if b_norm in seen:
                        log.debug("Pair skipped: b-text duplicate in %s/%s.", control_id, group_id)
                        # Roll back: remove the a-item's norm from seen since it was added above.
                        seen.discard(norm)
                        seq -= 1
                        continue
                    # Define b_probe_id before building either item so that
                    # paired_probe_id can be set symmetrically.  The runner
                    # looks for probe.get("paired_probe_id") to locate the
                    # partner's response for bias_consistency_v1 scoring.
                    b_probe_id = probe_id_str + "-b"
                    pair_id = f"pair-{probe_id_str}"
                    item["pair_id"] = pair_id
                    item["pair_member"] = "a"
                    item["paired_probe_id"] = b_probe_id
                    locale_pool[locale].append(item)
                    seen.add(b_norm)
                    b_item: dict[str, Any] = {
                        "probe_id": b_probe_id,
                        "control_id": control_id,
                        "locale": locale,
                        "prompt": filled_b_text,
                        "scorer": scorer,
                        "scorer_config": scorer_config,
                        "pair_id": pair_id,
                        "pair_member": "b",
                        "paired_probe_id": probe_id_str,
                        "provenance": {
                            "source": "generated",
                            "grammar_id": grammar_id,
                            "group_id": group_id,
                            "template_idx": t_idx,
                            "slots_filled": provenance_slots,
                            "seed": seed,
                            "variant": "b",
                        },
                    }
                    locale_pool[locale].append(b_item)
                else:
                    locale_pool[locale].append(item)

    # Trim locale pools to quota, then combine.
    # For paired controls, distribute in pair-units (n_target // 2 pairs total) so
    # rounding errors in individual locale quotas do not cause orphaned a-items or
    # a combined total that falls 2 short.
    all_pool_items = [it for pool in locale_pool.values() for it in pool]
    has_pairs = any(it.get("pair_member") for it in all_pool_items[:8])
    items: list[dict[str, Any]] = []

    if has_pairs:
        n_pairs_total = n_target // 2
        pair_quotas: dict[str, int] = {}
        assigned = 0
        for loc, ratio in locale_split.items():
            pool = locale_pool.get(loc, [])
            pool_pairs = len(pool) // 2
            wanted = round(n_pairs_total * ratio)
            pair_quotas[loc] = min(wanted, pool_pairs)
            assigned += pair_quotas[loc]
        # Redistribute any shortfall (locale had fewer pairs than wanted).
        shortfall = n_pairs_total - assigned
        for loc in locale_split:
            if shortfall <= 0:
                break
            pool = locale_pool.get(loc, [])
            pool_pairs = len(pool) // 2
            extra = pool_pairs - pair_quotas.get(loc, 0)
            give = min(extra, shortfall)
            pair_quotas[loc] = pair_quotas.get(loc, 0) + give
            shortfall -= give
        for loc in locale_split:
            quota_items = pair_quotas.get(loc, 0) * 2
            pool = locale_pool.get(loc, [])
            items.extend(pool[:quota_items])
    else:
        for loc, ratio in locale_split.items():
            quota = round(n_target * ratio)
            pool = locale_pool.get(loc, [])
            items.extend(pool[:quota])

    # Final guard: never exceed n_target; ensure no trailing orphan a-item.
    if len(items) > n_target:
        items = items[:n_target]
    if items and items[-1].get("pair_member") == "a":
        items = items[:-1]

    if near_dup_count > 0:
        log.info(
            "Control %s: %d near-duplicate pairs (edit distance <= 20) in %d generated items.",
            control_id,
            near_dup_count,
            len(items),
        )

    log.info(
        "Control %s: generated %d items (target %d).",
        control_id,
        len(items),
        n_target,
    )
    return items


# ---------------------------------------------------------------------------
# Validation pass
# ---------------------------------------------------------------------------

# Every scorer name that the MIZAN harness can dispatch.  If a generated
# item declares any other name it will silently score 0.0 at evaluation
# time, which is not a hard probe -- it is a broken one.
_VALID_SCORERS: frozenset[str] = frozenset({
    "keyword_refusal_v1",
    "refusal_integrity_v1",
    "factual_keywords_v1",
    "bias_consistency_v1",
    "injection_resistance_v1",
    "pii_non_disclosure_v1",
    "model_card_attestation_v1",
})

# Scorers whose config must contain a non-empty list under this key.
_KEYWORD_SCORER_REQUIRED_FIELD: dict[str, str] = {
    "factual_keywords_v1": "expected_keywords",
}

# Scorers that require a resolvable paired_probe_id field.
_PAIR_BASED_SCORERS: frozenset[str] = frozenset({"bias_consistency_v1"})


def _validate_items(items: list[dict[str, Any]], control_id: str) -> None:
    """Fail loudly if any item has a structural scorer violation.

    This runs after generation of each control's item list, before writing
    to disk.  Its purpose is to close the defect class where an item
    declares a scorer contract it cannot satisfy, causing it to score 0.0
    regardless of the model's response.

    Violations detected
    -------------------
    1. Scorer name not registered in the harness.
    2. factual_keywords_v1 config missing or empty expected_keywords.
    3. bias_consistency_v1 item missing paired_probe_id, or paired_probe_id
       not present in the generated item set.
    """
    probe_id_set: set[str] = {item["probe_id"] for item in items}
    violations: list[str] = []

    for item in items:
        probe_id = item["probe_id"]
        scorer = item.get("scorer", "")
        config = item.get("scorer_config", {})

        if scorer not in _VALID_SCORERS:
            violations.append(
                f"{probe_id}: unknown scorer {scorer!r} -- not registered in "
                f"the harness scorer dispatcher"
            )
            continue  # No further checks possible for this item.

        keyword_key = _KEYWORD_SCORER_REQUIRED_FIELD.get(scorer)
        if keyword_key is not None:
            keywords = config.get(keyword_key, [])
            if not keywords:
                violations.append(
                    f"{probe_id}: {scorer} requires a non-empty "
                    f"scorer_config.{keyword_key}; got {config!r}"
                )

        if scorer in _PAIR_BASED_SCORERS:
            paired_id = item.get("paired_probe_id")
            if not paired_id:
                violations.append(
                    f"{probe_id}: {scorer} requires paired_probe_id; "
                    f"field is absent or None"
                )
            elif paired_id not in probe_id_set:
                violations.append(
                    f"{probe_id}: paired_probe_id {paired_id!r} is not "
                    f"present in the generated item set for {control_id}"
                )

    if violations:
        log.error(
            "CORPUS VALIDATION FAILED -- %d violation(s) in control %s:",
            len(violations),
            control_id,
        )
        for v in violations:
            log.error("  %s", v)
        log.error(
            "Generation aborted.  A probe that always scores zero regardless "
            "of the model's response is not a hard probe, it is a broken one.  "
            "Fix the grammar's scorer / scorer_config before regenerating."
        )
        sys.exit(1)


def generate(
    seed: int,
    grammar_file: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, int]:
    """
    Generate corpus from all grammar files (or one specified file).

    Parameters
    ----------
    seed:
        Deterministic seed.  Same seed always produces byte-identical output.
    grammar_file:
        If provided, generate only from this one grammar file.
    output_dir:
        Directory to write generated JSON files into.  Defaults to
        OUTPUT_DIR (suites/generated/).  Pass a temporary directory in tests
        so suites/generated/ is never touched.

    Returns
    -------
    dict[str, int]
        Mapping from suite_id to the number of items generated.
    """
    dest = output_dir if output_dir is not None else OUTPUT_DIR
    dest.mkdir(parents=True, exist_ok=True)

    grammar_files = [grammar_file] if grammar_file else sorted(GRAMMARS_DIR.glob("*.grammar.json"))
    if not grammar_files:
        log.error("No grammar files found in %s.", GRAMMARS_DIR)
        sys.exit(1)

    results: dict[str, int] = {}

    for gf in grammar_files:
        log.info("Loading grammar: %s", gf.name)
        with gf.open(encoding="utf-8") as f:
            grammar = json.load(f)

        grammar_id: str = grammar["grammar_id"]
        all_items: list[dict[str, Any]] = []
        control_counts: dict[str, int] = {}

        controls: dict[str, Any] = grammar.get("controls", {})
        for control_id, control_def in controls.items():
            if control_id in ATTESTATION_ONLY_CONTROLS:
                log.info("Skipping attestation-only control: %s", control_id)
                continue

            items = _generate_control(grammar, control_id, control_def, seed)
            _validate_items(items, control_id)
            all_items.extend(items)
            control_counts[control_id] = len(items)

        # Assign suite_id from grammar_id (strip version suffix)
        suite_id = grammar_id.replace("-v1", "")
        output_path = dest / f"{suite_id}.generated.json"

        # Verify no exact duplicate probe_ids across the whole file
        probe_ids = [item["probe_id"] for item in all_items]
        if len(probe_ids) != len(set(probe_ids)):
            dupes = [pid for pid in probe_ids if probe_ids.count(pid) > 1]
            log.error("FATAL: Duplicate probe_ids detected: %s", set(dupes))
            sys.exit(1)

        output_data = {
            "grammar_id": grammar_id,
            "seed": seed,
            "total_items": len(all_items),
            "control_counts": control_counts,
            "items": all_items,
        }

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        log.info(
            "Wrote %d items to %s (controls: %s)",
            len(all_items),
            output_path,
            control_counts,
        )
        results[suite_id] = len(all_items)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate MIZAN evaluation corpus.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed.")
    parser.add_argument(
        "--grammar",
        type=Path,
        default=None,
        help="Generate from a single grammar file (default: all).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        dest="output_dir",
        help=(
            "Directory to write generated JSON files into "
            "(default: suites/generated/).  Pass a temporary directory "
            "in test invocations to keep suites/generated/ untouched."
        ),
    )
    args = parser.parse_args()

    log.info("Generating corpus with seed=%d", args.seed)
    results = generate(seed=args.seed, grammar_file=args.grammar, output_dir=args.output_dir)
    total = sum(results.values())
    log.info("Generation complete. Total items: %d across %d suites.", total, len(results))
    for suite_id, count in results.items():
        log.info("  %s: %d items", suite_id, count)


if __name__ == "__main__":
    main()
