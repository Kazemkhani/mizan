"""Tests for the data grounding and honesty gates.

The gate that never fires and the gate that always fires are equally useless.
These pin both edges.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from verify_grounding import SOURCE_MARKERS, IGNORABLE_NUMBER, NUMBER, mask  # noqa: E402


def numbers_flagged(line: str) -> list[str]:
    """Mirror the G3 decision for a single line."""
    if line.lstrip().startswith("#") or SOURCE_MARKERS.search(line):
        return []
    out = []
    for m in NUMBER.finditer(mask(line)):
        tok = m.group(0).strip()
        if IGNORABLE_NUMBER.match(tok.replace(",", "")):
            continue
        start = m.start()
        if start >= 2 and line[start - 1] == "-" and line[start - 2].isalpha():
            continue
        out.append(tok)
    return out


def test_bare_claim_is_flagged():
    assert numbers_flagged("Evaluation time falls by 80 percent.") == ["80 percent"]


def test_number_with_a_script_source_is_permitted():
    line = "Evaluation time falls by 80 percent, produced by scripts/prove_reduction.py."
    assert numbers_flagged(line) == []


def test_number_labelled_an_assumption_is_permitted():
    line = "Roughly 200 entities adopt it by year three [assumption: not measured]."
    assert numbers_flagged(line) == []


def test_number_with_an_official_source_and_read_date_is_permitted():
    line = "56 publishing entities, source: bayanat.ae, read on 19 August 2026."
    assert numbers_flagged(line) == []


def test_algorithm_name_is_not_a_claim():
    """SHA-256 is a name, not a figure."""
    assert numbers_flagged("Every probe carries a SHA-256 hash.") == []


def test_decision_reference_is_not_a_claim():
    assert numbers_flagged("Recorded as D-011 in the decisions log.") == []


def test_a_numeric_range_is_still_checked():
    """The hyphen exemption must not swallow a real claim such as 80-90.

    Note the token carries its unit: a bare two-digit number is treated as
    structural, but attaching "percent" makes it a claim.
    """
    assert numbers_flagged("Reduction lands between 80 and 90 percent.") == ["90 percent"]


def test_a_hyphenated_range_is_still_checked():
    assert numbers_flagged("Reduction lands at 80-90 percent.") == ["90 percent"]


def test_a_bare_small_integer_is_treated_as_structural():
    """Deliberate: prose is full of small counts. The unit is what makes a claim."""
    assert numbers_flagged("There are 5 use cases.") == []


def test_heading_is_skipped():
    assert numbers_flagged("## 80 percent reduction") == []


def test_fenced_and_inline_code_are_masked():
    assert numbers_flagged("Run `make test` and see 39 passed inside `39 passed`.") == []
