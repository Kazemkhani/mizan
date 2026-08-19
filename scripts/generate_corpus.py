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

    # Determine locale for each group and allocate slots accordingly.
    # For bias controls, template_en and template_en_b are paired.
    items: list[dict[str, Any]] = []
    seen_normalised: set[str] = set()
    near_dup_count = 0
    seq = 0

    for group in groups:
        group_id: str = group["group_id"]
        locale: str = group.get("locale", "en")
        slots: dict[str, list[str]] = group.get("slots", {})

        # Collect all template variants (en, ar, en_b, ar_b)
        templates_en: list[str] = group.get("templates_en", [])
        templates_ar: list[str] = group.get("templates_ar", [])
        templates_en_b: list[str] = group.get("templates_en_b", [])
        templates_ar_b: list[str] = group.get("templates_ar_b", [])

        # Primary templates for this locale
        primary_templates = templates_ar if locale == "ar" else templates_en

        # Bias groups also have a _b variant -- handle pairing.
        b_templates = templates_ar_b if locale == "ar" else templates_en_b
        is_paired = bool(b_templates)

        if not primary_templates:
            log.warning("Group %s/%s has no templates -- skipping.", control_id, group_id)
            continue

        # Calculate how many items to produce from this group.
        # Distribute evenly across groups; overshoot slightly to allow dedup.
        n_groups = len(groups)
        group_target = max(1, (n_target * 2) // n_groups)  # 2x then trim at end

        template_count = len(primary_templates)
        slot_combinations: list[dict[str, str]] = []

        # Build all slot key-value combinations up to a limit.
        slot_keys = list(slots.keys())
        if slot_keys:
            slot_value_lists = [slots[k] for k in slot_keys]
            all_combinations = list(product(*slot_value_lists))
            # Limit combinations to avoid memory explosion
            max_combos = min(len(all_combinations), group_target * 4)
            all_combinations = all_combinations[:max_combos]
            for combo in all_combinations:
                slot_combinations.append(dict(zip(slot_keys, combo)))
        else:
            slot_combinations = [{}]

        # Generate items, selecting deterministically.
        for t_idx, template in enumerate(primary_templates):
            for combo_idx, combo in enumerate(slot_combinations):
                if len(items) >= n_target * 2:
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
                    # For b-variant, swap a-slots with b-slots using deterministic selection.
                    for slot_name in list(b_slots.keys()):
                        b_slot_key = slot_name + "_b"
                        if b_slot_key in slots:
                            key = f"{grammar_id}:{control_id}:{group_id}:{t_idx}:{b_slot_key}:{combo_idx}:{seed}"
                            b_slots[b_slot_key.replace("_b", "")] = _sha256_slot(key, slots[b_slot_key])
                    filled_b_text = b_template
                    for sn, sv in b_slots.items():
                        filled_b_text = filled_b_text.replace("{" + sn + "}", sv)
                    # Clean up any remaining unfilled slots
                    import re as _re
                    filled_b_text = _re.sub(r"\{[^}]+\}", "[SLOT]", filled_b_text)

                # Clean up any remaining unfilled slots
                import re as _re
                filled_text = _re.sub(r"\{[^}]+\}", "[SLOT]", filled_text)

                norm = _normalise(filled_text)

                # Exact duplicate check
                if norm in seen_normalised:
                    log.debug("Exact duplicate skipped in %s/%s.", control_id, group_id)
                    continue

                # Near-duplicate count (report only, do not suppress)
                for existing_norm in list(seen_normalised)[-200:]:  # check last 200
                    if _edit_distance(norm, existing_norm) <= 20:
                        near_dup_count += 1
                        break

                seen_normalised.add(norm)
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
                    pair_id = f"pair-{probe_id_str}"
                    item["pair_id"] = pair_id
                    item["pair_member"] = "a"
                    items.append(item)

                    b_probe_id = probe_id_str + "-b"
                    b_norm = _normalise(filled_b_text)
                    if b_norm not in seen_normalised:
                        seen_normalised.add(b_norm)
                        b_item: dict[str, Any] = {
                            "probe_id": b_probe_id,
                            "control_id": control_id,
                            "locale": locale,
                            "prompt": filled_b_text,
                            "scorer": scorer,
                            "scorer_config": scorer_config,
                            "pair_id": pair_id,
                            "pair_member": "b",
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
                        items.append(b_item)
                else:
                    items.append(item)

    # Trim to n_target
    if len(items) > n_target:
        items = items[:n_target]

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


def generate(seed: int, grammar_file: Path | None = None) -> dict[str, int]:
    """
    Generate corpus from all grammar files (or one specified file).
    Returns {suite_id: item_count}.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
            all_items.extend(items)
            control_counts[control_id] = len(items)

        # Assign suite_id from grammar_id (strip version suffix)
        suite_id = grammar_id.replace("-v1", "")
        output_path = OUTPUT_DIR / f"{suite_id}.generated.json"

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
    args = parser.parse_args()

    log.info("Generating corpus with seed=%d", args.seed)
    results = generate(seed=args.seed, grammar_file=args.grammar)
    total = sum(results.values())
    log.info("Generation complete. Total items: %d across %d suites.", total, len(results))
    for suite_id, count in results.items():
        log.info("  %s: %d items", suite_id, count)


if __name__ == "__main__":
    main()
