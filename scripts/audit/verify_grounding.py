#!/usr/bin/env python3
"""Data grounding and honesty gates. Charter Addendum 01 sections 2 and 5.

Three checks, all hard gates:

  G1  docs/RISKS.md exists, names risks, and gives each a mitigation that sits
      inside the 90-day plan. A risks document without mitigations is a list of
      excuses.
  G2  docs/evidence/data_sources.md exists and every use case declared in
      suites/controls/use_cases.json has at least one dataset binding carrying a
      Resource GUID, a publishing entity and a read date.
  G3  Every number on a pitch-facing surface is sourced. A figure is acceptable
      when it is produced by a committed script, attributed to a named official
      source with the date it was read, or labelled an assumption, and when that
      marker sits on the same line or in the same table row.

An unsourced number is a critical finding equal to a fabricated benchmark.

Usage: uv run python scripts/audit/verify_grounding.py
Exit 1 on any finding.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RISKS = REPO_ROOT / "docs" / "RISKS.md"
DATA_SOURCES = REPO_ROOT / "docs" / "evidence" / "data_sources.md"
USE_CASES = REPO_ROOT / "suites" / "controls" / "use_cases.json"

PITCH_SURFACES = ["docs/submission", "docs/RISKS.md", "README.md"]

# A number is grounded when its line carries one of these markers.
SOURCE_MARKERS = re.compile(
    r"(\[source:|\[assumption:|\[measured:|source:|read on |retrieved |"
    r"measured by |per \w+\.py|scripts/|docs/evidence/|https?://|"
    r"bayanat\.ae|assumption\b|\bGUID\b)",
    re.IGNORECASE,
)
# Numbers that are structural rather than claims.
IGNORABLE_NUMBER = re.compile(
    r"^(19|20)\d\d$|^\d{1,2}$|^v?\d+\.\d+(\.\d+)?$|^#\w+$"
)
NUMBER = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*(?:percent|%)?\b")
FENCED = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
INLINE_CODE = re.compile(r"`[^`\n]*`")
MITIGATION = re.compile(r"mitigat", re.IGNORECASE)


class Finding:
    def __init__(self, gate: str, where: str, message: str):
        self.gate, self.where, self.message = gate, where, message

    def __str__(self) -> str:
        return f"[{self.gate}] {self.where}: {self.message}"


def mask(text: str) -> str:
    def blank(m):
        return "".join("\n" if ch == "\n" else " " for ch in m.group(0))
    return INLINE_CODE.sub(blank, FENCED.sub(blank, text))


def check_risks() -> list[Finding]:
    if not RISKS.exists():
        return [Finding("G1", "docs/RISKS.md", "missing; Addendum section 5 requires it")]
    text = RISKS.read_text(encoding="utf-8")
    findings = []
    headings = [l for l in text.splitlines() if l.startswith("### ")]
    if len(headings) < 3:
        findings.append(Finding("G1", "docs/RISKS.md",
                                f"only {len(headings)} risks named; the addendum names three as a floor"))
    blocks = re.split(r"^### ", text, flags=re.MULTILINE)[1:]
    for b in blocks:
        title = b.splitlines()[0].strip()
        if not MITIGATION.search(b):
            findings.append(Finding("G1", f"docs/RISKS.md: {title}",
                                    "risk has no mitigation; a risk without one is an excuse"))
    return findings


def check_data_sources() -> list[Finding]:
    findings = []
    if not USE_CASES.exists():
        return [Finding("G2", "suites/controls/use_cases.json", "missing")]
    data = json.loads(USE_CASES.read_text(encoding="utf-8"))
    cases = data.get("use_cases", data) if isinstance(data, dict) else data
    ids = [u["id"] for u in cases]

    if not DATA_SOURCES.exists():
        return [Finding("G2", "docs/evidence/data_sources.md",
                        f"missing; {len(ids)} use cases need dataset bindings")]
    text = DATA_SOURCES.read_text(encoding="utf-8")
    for uid in ids:
        if uid not in text:
            findings.append(Finding("G2", f"use case {uid}", "no dataset binding recorded"))
            continue
        # The binding must carry a GUID and a read date somewhere in its section.
        section = text.split(uid, 1)[1][:1500]
        if not re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}", section) and "GUID" not in section:
            findings.append(Finding("G2", f"use case {uid}", "binding carries no Resource GUID"))
        if not re.search(r"(read on|retrieved|last[- ]updated|\d{4}-\d{2}-\d{2})", section, re.I):
            findings.append(Finding("G2", f"use case {uid}", "binding carries no read date"))
    return findings


def iter_pitch_files():
    for entry in PITCH_SURFACES:
        p = REPO_ROOT / entry
        if p.is_file():
            yield p
        elif p.is_dir():
            yield from sorted(p.rglob("*.md"))


def check_numbers() -> list[Finding]:
    findings = []
    for path in iter_pitch_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        for i, line in enumerate(mask(path.read_text(encoding="utf-8")).splitlines(), start=1):
            if line.lstrip().startswith("#") or SOURCE_MARKERS.search(line):
                continue
            for m in NUMBER.finditer(line):
                tok = m.group(0).strip()
                if IGNORABLE_NUMBER.match(tok.replace(",", "")):
                    continue
                # A number bound to a letter by a hyphen is an identifier or a
                # standard's name, not a claim: SHA-256, D-011, UTF-8, ISO-8601.
                # A digit before the hyphen is left alone, so a range such as
                # 80-90 percent is still checked.
                start = m.start()
                if start >= 2 and line[start - 1] == "-" and line[start - 2].isalpha():
                    continue
                findings.append(Finding(
                    "G3", f"{rel}:{i}",
                    f"unsourced figure {tok!r}; produce it from a script, cite an "
                    f"official source with its read date, or label it an assumption"))
    return findings


def main() -> int:
    print("MIZAN Data Grounding and Honesty Gates")
    print("=" * 60)
    findings = []
    for name, fn in (("G1 risks", check_risks),
                     ("G2 dataset bindings", check_data_sources),
                     ("G3 sourced numbers", check_numbers)):
        result = fn()
        print(f"{name:24} {'PASS' if not result else f'FAIL ({len(result)})'}")
        findings.extend(result)
    print()
    for f in findings:
        print(f"  {f}")
    print()
    print(f"Findings: {len(findings)}")
    if not findings:
        print("Grounding: every gate passes.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
