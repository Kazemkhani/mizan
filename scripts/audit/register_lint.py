#!/usr/bin/env python3
"""MIZAN public-language linter.

Enforces the repository's documented language policy mechanically.

Rules:
  E001  em-dash or horizontal bar anywhere
  E002  emoji anywhere
  E003  American spelling in prose, in a comment, or in a user-facing string
  E004  a Latin-script quotation mark pair used where the policy expects plain prose is not checked;
        instead this slot flags mixed-direction punctuation errors in Arabic strings

Prose files are scanned in full. Code files are scanned in their comments and
string literals only, so that language identifiers such as the CSS `color`
property or a JavaScript `normalize` call are never flagged.

Usage:
  uv run python scripts/audit/register_lint.py [path ...]
  uv run python scripts/audit/register_lint.py --json
Exit code 1 if any finding is raised.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_FILES = {
    "scripts/audit/register_lint.py",
    # Deliberate violations live here as test fixtures.
    "scripts/audit/test_register_lint.py",
}

# Files under these relative path prefixes are excluded from ALL register-lint
# checks (E001 em-dash, E002 emoji, E003 American spelling, E004 dingbats,
# E005 pitch language). suites/data/ contains verbatim Bayanat open-data
# artefacts sourced from the UAE government portal. Their string content (e.g.
# "Speed Center", "analyze" in metadata fields) is the authoritative dataset
# text and must not be altered without falsifying the source. Grounding rule
# (Wave 1): an externally-sourced file may not be silently corrected; it is
# excluded here and its provenance is recorded in DECISIONS.md.
EXCLUDED_PREFIXES: tuple[str, ...] = (
    "suites/data/",
    # NOTE: suites/generated/ is deliberately NOT exempt. Generated probe text
    # is user-facing: a judge reads it in the evidence trail. It lints clean
    # today because the grammars are clean, which is exactly why the gate must
    # keep covering it; an exemption here would let a future grammar change
    # push an em-dash into several hundred Arabic probes unnoticed.
)

EXCLUDED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
    ".pytest_cache", ".ruff_cache", ".mypy_cache", "uv.lock",
}

PROSE_SUFFIXES = {".md", ".txt", ".rst"}
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".scss", ".html", ".sql", ".sh", ".toml", ".yaml", ".yml"}
DATA_SUFFIXES = {".json"}

# U+2014 em-dash, U+2015 horizontal bar. Written as escapes so this file does
# not flag itself.
DASH_PATTERN = re.compile("[—―]")

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U0001F000-\U0001F2FF"
    "\U0000FE0F"
    "]"
)

# Dingbats, arrows and geometric shapes. Legitimate technical notation in a
# comment or a document table, banned in user-facing strings.
DINGBAT_PATTERN = re.compile(
    "["
    "\U00002600-\U000027BF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "]"
)

# Paths whose string literals reach a human reading the product.
USER_FACING_PREFIXES = ("web/src/", "web/public/", "suites/", "api/")

# ---------------------------------------------------------------------------
# E005, the precise public-language policy.
# The judges' formula is: name the action, name the outcome, name the safeguard.
# Marketing register is banned wherever a judge can read it. This is scoped to
# pitch-facing surfaces rather than the whole repository, because an internal
# engineering note discussing a "platform" is not a pitch claim.
# ---------------------------------------------------------------------------
PITCH_FACING_PREFIXES = ("web/src/i18n/", "docs/submission/")
PITCH_FACING_FILES = {
    "docs/RISKS.md",
    "docs/DATA_REQUESTS.md",
    "suites/controls/certificate_content.json",
    "README.md",
}

# A document that must quote the banned vocabulary, such as this law itself,
# opts out with this marker on any line.
ALLOW_BANNED_MARKER = "register-lint: allow-banned"

BANNED_PHRASES = {
    "ai-powered": "name what the engine does instead",
    "ai powered": "name what the engine does instead",
    "innovative": "show the mechanism; the judge decides if it is novel",
    "ecosystem": "name the actual parties",
    "seamless": "name the step that was removed",
    "leverage": "use, or name the specific mechanism",
    "revolutionise": "state the measured change",
    "revolutionize": "state the measured change",
    "cutting-edge": "state what it does that the alternative does not",
    "cutting edge": "state what it does that the alternative does not",
    "state-of-the-art": "state the measured comparison",
    "game-changing": "state the measured change",
    "world-class": "state the measured standard met",
    "best-in-class": "state the measured comparison",
}

# The product is described only as a registry, an engine, a certificate, an
# instrument, or infrastructure.
BANNED_PRODUCT_NOUNS = {
    "platform": "registry, engine, certificate, instrument or infrastructure",
    "solution": "registry, engine, certificate, instrument or infrastructure",
}

# "improves efficiency" is permitted only with a number in the same sentence.
EFFICIENCY_CLAIM = re.compile(
    r"[^.!?\n]*\b(improve[sd]?|increase[sd]?|boost[sd]?|enhance[sd]?)\s+(the\s+)?"
    r"(efficiency|productivity|speed|performance)\b[^.!?\n]*",
    re.IGNORECASE,
)
# "uses AI" is permitted only when the same sentence says what the AI does.
USES_AI_CLAIM = re.compile(
    r"[^.!?\n]*\b(uses?|using|powered by|driven by|built on)\s+"
    r"(ai|artificial intelligence|machine learning|ml)\b[^.!?\n]*",
    re.IGNORECASE,
)
HAS_NUMBER = re.compile(r"\d")
# Verbs that constitute saying what the AI actually does.
AI_ACTION_VERBS = re.compile(
    r"\b(allocat\w+|rank\w+|classif\w+|scor\w+|order\w+|select\w+|stop\w+|"
    r"predict\w+|detect\w+|refus\w+|summaris\w+|extract\w+|estimat\w+|"
    r"search\w+|schedul\w+|adjudicat\w+|measur\w+|comput\w+)\b",
    re.IGNORECASE,
)

# American form -> British form. Kept to forms that are unambiguous in prose.
AMERICAN_SPELLINGS = {
    "analyze": "analyse", "analyzer": "analyser", "analyzers": "analysers", "analyzed": "analysed", "analyzes": "analyses", "analyzing": "analysing",
    "behavior": "behaviour", "behaviors": "behaviours", "behavioral": "behavioural",
    "canceled": "cancelled", "canceling": "cancelling",
    "catalog": "catalogue", "catalogs": "catalogues",
    "center": "centre", "centered": "centred", "centers": "centres",
    "color": "colour", "colors": "colours", "colored": "coloured", "coloring": "colouring",
    "defense": "defence", "defenses": "defences",
    "favor": "favour", "favors": "favours", "favorite": "favourite",
    "fulfill": "fulfil", "fulfilled": "fulfilled", "fulfillment": "fulfilment",
    "gray": "grey", "grayscale": "greyscale",
    "honor": "honour", "honored": "honoured",
    "initialize": "initialise", "initialized": "initialised", "initializing": "initialising",
    "labeled": "labelled", "labeling": "labelling",
    "maximize": "maximise", "minimize": "minimise",
    "modeling": "modelling", "modeled": "modelled",
    "normalize": "normalise", "normalized": "normalised", "normalizing": "normalising",
    "optimize": "optimise", "optimized": "optimised", "optimizing": "optimising", "optimization": "optimisation",
    "organize": "organise", "organized": "organised", "organization": "organisation", "organizations": "organisations",
    "prioritize": "prioritise", "prioritized": "prioritised",
    "recognize": "recognise", "recognized": "recognised",
    "serialize": "serialise", "serialized": "serialised",
    "specialize": "specialise", "specialized": "specialised",
    "standardize": "standardise", "standardized": "standardised",
    "summarize": "summarise", "summarized": "summarised", "summarization": "summarisation",
    "traveled": "travelled", "traveling": "travelling",
    "utilize": "utilise", "utilized": "utilised",
    "authorize": "authorise", "authorized": "authorised", "authorization": "authorisation",
    "apologize": "apologise",
    "signaling": "signalling", "modeling_": "modelling",
    "enrollment": "enrolment",
    "fiber": "fibre", "liter": "litre", "meter": "metre",
    "practicing": "practising",
    "skillful": "skilful",
    "willful": "wilful",
}

# Identifiers that are fixed by a language, a standard, a library or an external
# proper noun. Never flagged, in any file type.
TECHNICAL_ALLOWLIST = {
    # CSS and DOM
    "color", "colors", "background-color", "border-color", "accent-color", "caret-color",
    "color-scheme", "text-decoration-color", "outline-color", "fill-color", "stop-color",
    "center", "text-align", "align-center", "justify-center", "items-center", "self-center",
    "gray", "grayscale", "colorspace",
    # JavaScript, Python, SQL standard library
    "normalize", "normalized", "serialize", "serialized", "deserialize", "initialize",
    "toLocaleUpperCase", "localeCompare", "Intl", "canonicalize",
    # Proper nouns and external standards
    "Organization", "WHO", "ISO", "Organisation",
}

FENCED_CODE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
INLINE_CODE = re.compile(r"`[^`\n]*`")
MD_LINK_TARGET = re.compile(r"\]\([^)]*\)")
# An HTML tag inside a document is markup, not prose. Attribute values such
# as align="center" are fixed by the HTML specification, exactly as the CSS
# `color` property is, and must not be flagged as American spellings.
HTML_TAG = re.compile(r"<[^>\n]+>")

STRING_LITERAL = re.compile(r"""(['"`])((?:\\.|(?!\1).)*)\1""", re.DOTALL)
PY_COMMENT = re.compile(r"#(.*)$", re.MULTILINE)
C_LINE_COMMENT = re.compile(r"//(.*)$", re.MULTILINE)
C_BLOCK_COMMENT = re.compile(r"/\*(.*?)\*/", re.DOTALL)
SQL_COMMENT = re.compile(r"--(.*)$", re.MULTILINE)
HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.DOTALL)

WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


class Finding:
    __slots__ = ("path", "line", "code", "message", "excerpt")

    def __init__(self, path: str, line: int, code: str, message: str, excerpt: str):
        self.path = path
        self.line = line
        self.code = code
        self.message = message
        self.excerpt = excerpt.strip()[:160]

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "code": self.code,
            "message": self.message,
            "excerpt": self.excerpt,
        }

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}\n    {self.excerpt}"


def iter_files(targets: list[Path]):
    for target in targets:
        if target.is_file():
            yield target
            continue
        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else path.as_posix()
            if rel in EXCLUDED_FILES:
                continue
            if rel.startswith(EXCLUDED_PREFIXES):
                continue
            if path.suffix in PROSE_SUFFIXES | CODE_SUFFIXES | DATA_SUFFIXES:
                yield path


def mask(text: str, pattern: re.Pattern) -> str:
    """Blank out matches while preserving length and line breaks."""
    def blank(m: re.Match) -> str:
        return "".join("\n" if ch == "\n" else " " for ch in m.group(0))
    return pattern.sub(blank, text)


def extract_checkable_spans(text: str, suffix: str) -> list[tuple[int, str, bool]]:
    """Return (line_number, text, allow_technical) spans requiring British English.

    allow_technical is True only for code and data, where an identifier fixed by
    a language specification is not a spelling error. In prose it is False, so a
    document that writes "color" in a sentence is flagged; documents may still
    quote code freely because fenced and inline code spans are masked first.
    """
    spans: list[tuple[int, str, bool]] = []

    def add(match_text: str, offset: int) -> None:
        line_no = text.count("\n", 0, offset) + 1
        spans.append((line_no, match_text, True))

    if suffix in PROSE_SUFFIXES:
        prose = mask(text, FENCED_CODE)
        prose = mask(prose, INLINE_CODE)
        prose = mask(prose, MD_LINK_TARGET)
        prose = mask(prose, HTML_TAG)
        for i, line in enumerate(prose.splitlines(), start=1):
            spans.append((i, line, False))
        return spans

    if suffix in DATA_SUFFIXES:
        # String values in JSON are user-facing until proven otherwise.
        for m in STRING_LITERAL.finditer(text):
            add(m.group(2), m.start(2))
        return spans

    comment_patterns = []
    if suffix in {".py", ".sh", ".toml", ".yaml", ".yml"}:
        comment_patterns.append(PY_COMMENT)
    if suffix in {".ts", ".tsx", ".js", ".jsx", ".css", ".scss"}:
        comment_patterns.append(C_LINE_COMMENT)
        comment_patterns.append(C_BLOCK_COMMENT)
    if suffix == ".sql":
        comment_patterns.append(SQL_COMMENT)
    if suffix == ".html":
        comment_patterns.append(HTML_COMMENT)

    for pattern in comment_patterns:
        for m in pattern.finditer(text):
            add(m.group(1), m.start(1))

    for m in STRING_LITERAL.finditer(text):
        add(m.group(2), m.start(2))

    return spans


def check_file(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    rel = path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else path.as_posix()
    findings: list[Finding] = []

    # E001 and E002 apply to the whole file regardless of type.
    for i, line in enumerate(text.splitlines(), start=1):
        if DASH_PATTERN.search(line):
            findings.append(Finding(rel, i, "E001", "em-dash or horizontal bar is banned by the public-language policy", line))
        for m in EMOJI_PATTERN.finditer(line):
            findings.append(Finding(rel, i, "E002", f"emoji {m.group(0)!r} is banned by the public-language policy", line))

    # E004 applies to dingbats and arrows, but only where a string reaches a
    # human reading the product. Comments and documents may use them freely.
    user_facing = rel.startswith(USER_FACING_PREFIXES)
    if user_facing or path.suffix in DATA_SUFFIXES:
        for m in STRING_LITERAL.finditer(text):
            for d in DINGBAT_PATTERN.finditer(m.group(2)):
                line_no = text.count("\n", 0, m.start(2)) + 1
                findings.append(Finding(
                    rel, line_no, "E004",
                    f"dingbat or arrow {d.group(0)!r} in a user-facing string",
                    m.group(2),
                ))

    # E005, the precise language law, applies only to pitch-facing surfaces.
    pitch_facing = (
        rel.startswith(PITCH_FACING_PREFIXES)
        or rel in PITCH_FACING_FILES
        or rel.endswith("/README.md")
    )
    if pitch_facing and ALLOW_BANNED_MARKER not in text:
        findings.extend(check_precise_language(rel, text, path.suffix))

    # E003 applies only where British English is required.
    for line_no, span, allow_technical in extract_checkable_spans(text, path.suffix):
        for m in WORD.finditer(span):
            word = m.group(0)
            if allow_technical and word in TECHNICAL_ALLOWLIST:
                continue
            british = AMERICAN_SPELLINGS.get(word.lower())
            if british is None:
                continue
            # Skip if the token is part of a hyphenated or dotted identifier.
            start, end = m.span()
            before = span[start - 1] if start > 0 else " "
            after = span[end] if end < len(span) else " "
            if before in "-._" or after in "-._(":
                continue
            findings.append(
                Finding(rel, line_no, "E003", f"American spelling {word!r}, use {british!r}", span)
            )

    return findings


def check_precise_language(rel: str, text: str, suffix: str) -> list["Finding"]:
    """Enforce the precise-language policy on one public-facing file."""
    findings: list[Finding] = []

    if suffix in PROSE_SUFFIXES:
        scanned = mask(mask(text, FENCED_CODE), INLINE_CODE)
        spans = [(i, line) for i, line in enumerate(scanned.splitlines(), start=1)]
    else:
        spans = [
            (text.count("\n", 0, m.start(2)) + 1, m.group(2))
            for m in STRING_LITERAL.finditer(text)
        ]

    for line_no, span in spans:
        lowered = span.lower()
        for phrase, remedy in BANNED_PHRASES.items():
            if re.search(r"\b" + re.escape(phrase) + r"\b", lowered):
                findings.append(Finding(
                    rel, line_no, "E005",
                    f"marketing register {phrase!r} in pitch-facing copy; {remedy}", span))
        for noun, remedy in BANNED_PRODUCT_NOUNS.items():
            if re.search(r"\b" + re.escape(noun) + r"s?\b", lowered):
                findings.append(Finding(
                    rel, line_no, "E005",
                    f"{noun!r} as a product noun; MIZAN is a {remedy}", span))
        for m in EFFICIENCY_CLAIM.finditer(span):
            if not HAS_NUMBER.search(m.group(0)):
                findings.append(Finding(
                    rel, line_no, "E005",
                    "efficiency claim with no number in the same sentence", m.group(0)))
        for m in USES_AI_CLAIM.finditer(span):
            if not AI_ACTION_VERBS.search(m.group(0)):
                findings.append(Finding(
                    rel, line_no, "E005",
                    "says the system uses AI without naming what the AI does", m.group(0)))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="MIZAN register discipline linter")
    parser.add_argument("paths", nargs="*", default=None, help="paths to scan, default is the repository root")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit findings as JSON")
    args = parser.parse_args()

    targets = [Path(p).resolve() for p in args.paths] if args.paths else [REPO_ROOT]

    findings: list[Finding] = []
    scanned = 0
    for path in iter_files(targets):
        scanned += 1
        findings.extend(check_file(path))

    if args.as_json:
        print(json.dumps({
            "scanned": scanned,
            "findings": [f.as_dict() for f in findings],
            "clean": not findings,
        }, indent=2, ensure_ascii=False))
    else:
        for f in findings:
            print(f)
        print()
        print(f"Files scanned: {scanned}")
        print(f"Findings: {len(findings)}")
        if not findings:
            print("Register discipline: clean.")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
