"""Regression tests for the register discipline linter.

A linter that never fires is worse than no linter, because it manufactures
false confidence. These tests assert that each rule fires on a real violation
and stays silent on legitimate code.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from register_lint import check_file  # noqa: E402

EM_DASH = "—"


def write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def codes(path: Path) -> list[str]:
    return [f.code for f in check_file(path)]


def test_em_dash_is_caught_in_prose(tmp_path):
    path = write(tmp_path, "a.md", f"A sentence {EM_DASH} with a dash.\n")
    assert "E001" in codes(path)


def test_em_dash_is_caught_in_code(tmp_path):
    path = write(tmp_path, "a.py", f'# A comment {EM_DASH} with a dash\n')
    assert "E001" in codes(path)


def test_emoji_is_caught(tmp_path):
    path = write(tmp_path, "a.md", "Shipped \U0001F680\n")
    assert "E002" in codes(path)


def test_american_spelling_caught_in_prose(tmp_path):
    path = write(tmp_path, "a.md", "We must optimize the color of the center panel.\n")
    found = [f.message for f in check_file(path)]
    assert any("optimize" in m for m in found)
    assert any("color" in m for m in found)
    assert any("center" in m for m in found)


def test_prose_may_quote_code_without_penalty(tmp_path):
    body = "Set the `color` property.\n\n```css\n.a { color: navy; text-align: center; }\n```\n"
    path = write(tmp_path, "a.md", body)
    assert codes(path) == []


def test_python_comment_on_first_line_is_scanned(tmp_path):
    """This was a real defect: the comment pattern lacked re.MULTILINE, so only
    a comment on the final line of a file was ever examined."""
    path = write(tmp_path, "a.py", "# Check the behavior here\nx = 1\ny = 2\n")
    assert "E003" in codes(path)


def test_user_facing_string_is_scanned(tmp_path):
    path = write(tmp_path, "a.py", 'LABEL = "Please analyze the model"\n')
    assert "E003" in codes(path)


def test_language_identifiers_are_not_flagged(tmp_path):
    path = write(tmp_path, "a.css", ".panel { color: navy; text-align: center; }\n")
    assert codes(path) == []


def test_javascript_builtin_is_not_flagged(tmp_path):
    path = write(tmp_path, "a.ts", "const v = value.normalize();\n")
    assert codes(path) == []


def test_correct_british_prose_is_clean(tmp_path):
    body = "The evaluation centre optimises the colour scheme and analyses behaviour.\n"
    path = write(tmp_path, "a.md", body)
    assert codes(path) == []


def test_arabic_prose_is_not_mangled(tmp_path):
    path = write(tmp_path, "a.md", "ميزان هي البنية التحتية للثقة.\n")
    assert codes(path) == []


def test_tick_in_a_code_comment_is_permitted(tmp_path):
    """A tick documenting a contrast grade is technical notation, not an emoji."""
    path = write(tmp_path, "a.css", "/* Gold on navy: 9.79:1 \u2713 AAA */\n.a { color: gold; }\n")
    assert codes(path) == []


def test_arrow_in_prose_is_permitted(tmp_path):
    path = write(tmp_path, "a.md", "Submission \u2192 adjudication \u2192 certificate.\n")
    assert codes(path) == []


def test_true_emoji_is_still_caught_anywhere(tmp_path):
    path = write(tmp_path, "a.css", "/* Shipped \U0001F680 */\n")
    assert "E002" in codes(path)


def test_tick_in_a_string_catalogue_is_caught(tmp_path):
    """The same tick that is fine in a comment is a checkmark bullet in the UI,
    which the design doctrine bans as a generated-output tell."""
    path = write(tmp_path, "en.json", '{"status": "Certified ✓"}\n')
    assert "E004" in codes(path)


# ---------------------------------------------------------------------------
# E005, the precise language law. Charter Addendum 01 section 4.
# ---------------------------------------------------------------------------

def pitch(tmp_path: Path, body: str, name: str = "README.md") -> Path:
    """A pitch-facing surface. README.md is in scope by name."""
    return write(tmp_path, name, body)


def test_marketing_adjective_is_caught(tmp_path):
    assert "E005" in codes(pitch(tmp_path, "An innovative approach to compliance.\n"))


def test_ai_powered_is_caught(tmp_path):
    assert "E005" in codes(pitch(tmp_path, "An AI-powered registry.\n"))


def test_platform_as_product_noun_is_caught(tmp_path):
    assert "E005" in codes(pitch(tmp_path, "MIZAN is a compliance platform.\n"))


def test_solution_as_product_noun_is_caught(tmp_path):
    assert "E005" in codes(pitch(tmp_path, "Our solution adjudicates models.\n"))


def test_efficiency_claim_without_a_number_is_caught(tmp_path):
    assert "E005" in codes(pitch(tmp_path, "MIZAN improves efficiency for federal entities.\n"))


def test_efficiency_claim_with_a_number_is_permitted(tmp_path):
    body = "MIZAN improves evaluation efficiency by 80 percent, measured by the proof script.\n"
    assert codes(pitch(tmp_path, body)) == []


def test_uses_ai_without_saying_what_is_caught(tmp_path):
    assert "E005" in codes(pitch(tmp_path, "The registry uses AI to help government entities.\n"))


def test_uses_ai_with_the_action_named_is_permitted(tmp_path):
    body = "The engine uses a bandit allocator that ranks test suites by information gain.\n"
    assert codes(pitch(tmp_path, body)) == []


def test_precise_language_law_is_scoped_to_pitch_surfaces(tmp_path):
    """An internal engineering note may say platform; it is not a pitch claim."""
    path = write(tmp_path, "notes.md", "The platform layer is innovative here.\n")
    assert "E005" not in codes(path)


def test_allow_banned_marker_exempts_a_document(tmp_path):
    body = "<!-- register-lint: allow-banned -->\nBanned words include innovative and platform.\n"
    assert "E005" not in codes(pitch(tmp_path, body))


def test_compliant_pitch_copy_is_clean(tmp_path):
    body = (
        "MIZAN is a registry. The engine allocates evaluation budget across test "
        "suites and stops when the confidence bound separates from the threshold. "
        "Every certificate cites the evidence hash behind each control verdict.\n"
    )
    assert codes(pitch(tmp_path, body)) == []


def test_html_attribute_in_a_document_is_not_prose(tmp_path):
    """align="center" is HTML specification vocabulary, like the CSS color
    property. Flagging it was a gate defect, not a document defect."""
    path = write(tmp_path, "a.md", '<div align="center">\n\nThe evaluation centre.\n\n</div>\n')
    assert codes(path) == []


def test_american_spelling_in_html_tag_body_is_still_caught(tmp_path):
    """Masking the tag must not mask the text between tags."""
    path = write(tmp_path, "a.md", '<div align="center">\n\nWe optimize the colour.\n\n</div>\n')
    assert "E003" in codes(path)
