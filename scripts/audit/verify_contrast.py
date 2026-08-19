#!/usr/bin/env python3
"""Independent WCAG contrast verification for the MIZAN token layer.

AUDITOR does not accept a stated contrast ratio. This recomputes every pairing
from the hex values actually present in web/src/styles/tokens.css, so a ratio
claimed in a report and a ratio the stylesheet can produce cannot diverge.

Usage: uv run python scripts/audit/verify_contrast.py
Exit 1 if any required pairing fails its threshold or any token is missing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKENS = REPO_ROOT / "web" / "src" / "styles" / "tokens.css"

ROOT_BLOCK = re.compile(r":root\s*\{(.*?)\n\}", re.DOTALL)
DECL = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")
VAR_REF = re.compile(r"var\(\s*(--[a-z0-9-]+)\s*(?:,[^)]*)?\)")
HEX = re.compile(r"#[0-9a-fA-F]{3,8}")


def load_root_tokens(text: str) -> dict[str, str]:
    """Parse the first :root block only.

    tokens.css also defines a [data-theme="inverse"] block for certificate print,
    which redefines --surface-raised to #FFFFFF. Reading declarations file-wide
    would compare application text against the print background and report a
    failure that the application shell cannot actually produce.
    """
    match = ROOT_BLOCK.search(text)
    if match is None:
        return {}
    return {name: value.strip() for name, value in DECL.findall(match.group(1))}


def resolve(name: str, tokens: dict[str, str], depth: int = 0) -> str | None:
    """Follow a var() chain down to a literal hex value."""
    if depth > 12 or name not in tokens:
        return None
    value = tokens[name]
    hex_match = HEX.search(value)
    if hex_match:
        return hex_match.group(0)
    ref = VAR_REF.search(value)
    if ref:
        return resolve(ref.group(1), tokens, depth + 1)
    return None


def srgb_to_linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 8:
        h = h[:6]
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)


def ratio(fg: str, bg: str) -> float:
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def grade(r: float, large_text: bool = False) -> str:
    if large_text:
        return "AAA" if r >= 4.5 else "AA" if r >= 3.0 else "FAIL"
    return "AAA" if r >= 7.0 else "AA" if r >= 4.5 else "FAIL"


def main() -> int:
    if not TOKENS.exists():
        print(f"MISSING: {TOKENS}")
        return 1

    text = TOKENS.read_text(encoding="utf-8")
    tokens = load_root_tokens(text)
    print(f"Declarations parsed from the :root block: {len(tokens)}")
    print()

    # Every pairing that carries text in the application shell. The threshold is
    # the WCAG minimum for the role, not the value the report hopes to hit.
    required = [
        ("--text-primary", "--surface-base", "body text on page", False),
        ("--text-secondary", "--surface-base", "secondary text", False),
        ("--text-tertiary", "--surface-base", "tertiary text", False),
        ("--text-primary", "--surface-raised", "body text on raised surface", False),
        ("--text-secondary", "--surface-raised", "secondary on raised surface", False),
        ("--text-primary", "--surface-sunken", "body text on sunken surface", False),
    ]

    # Accent tokens are discovered rather than assumed, because their names are
    # ATELIER's to choose and a rename must not silently skip a check.
    for name in sorted(tokens):
        if name.startswith(("--text-accent", "--text-gold", "--accent-")):
            required.append((name, "--surface-base", f"{name} on page", False))
            required.append((name, "--surface-raised", f"{name} on raised surface", False))

    # Adjudication states. Each state exposes a text colour, a chip surface and a
    # border. The text must clear AA against its own chip and against both page
    # surfaces, because a status label appears in the registry table and inside a
    # chip. The border is a non-text boundary and takes the 3:1 threshold.
    states = sorted({
        name[len("--state-"):].rsplit("-", 1)[0] if name.endswith(("-text", "-surface", "-border", "-muted"))
        else name[len("--state-"):]
        for name in tokens if name.startswith("--state-")
    })
    for state in states:
        text_token = f"--state-{state}-text"
        chip_token = f"--state-{state}-surface"
        border_token = f"--state-{state}-border"
        if text_token in tokens:
            if chip_token in tokens:
                required.append((text_token, chip_token, f"{state} label on its chip", False))
            required.append((text_token, "--surface-base", f"{state} label on page", False))
            required.append((text_token, "--surface-raised", f"{state} label on raised surface", False))
        if border_token in tokens and chip_token in tokens:
            required.append((border_token, chip_token, f"{state} chip border", True))

    findings: list[str] = []
    checked = 0

    for fg_name, bg_name, role, large in required:
        fg = resolve(fg_name, tokens)
        bg = resolve(bg_name, tokens)
        if fg is None or bg is None:
            missing = fg_name if fg is None else bg_name
            findings.append(f"UNRESOLVED TOKEN {missing} (needed for {role})")
            print(f"[FAIL] unresolved {missing}  ({role})")
            continue
        checked += 1
        r = ratio(fg, bg)
        g = grade(r, large)
        status = "ok  " if g != "FAIL" else "FAIL"
        print(f"[{status}] {r:5.2f}:1  {g:4}  {role}")
        print(f"          {fg_name} {fg} on {bg_name} {bg}")
        if g == "FAIL":
            findings.append(f"CONTRAST FAIL {r:.2f}:1 for {role}: {fg_name} on {bg_name}")

    print()
    print(f"Pairings verified: {checked}")
    if findings:
        print(f"Findings: {len(findings)}")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("Contrast: all required pairings meet their WCAG threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
