"""Licence and attribution checks for redistributed project assets."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "suites" / "data"
FONT_DIR = REPO_ROOT / "web" / "public" / "fonts"

CC_BY_4 = "https://creativecommons.org/licenses/by/4.0/"
PORTAL_TERMS = {
    "https://data.ajman.ae/terms/terms-and-conditions/",
    "https://opendata.fcsc.gov.ae/p/terms-of-use",
}


def test_every_cached_dataset_has_complete_attribution() -> None:
    manifests = sorted(DATA_DIR.glob("*.manifest.json"))
    caches = sorted(
        path
        for path in DATA_DIR.glob("*.json")
        if not path.name.endswith((".manifest.json", ".meta.json"))
    )

    assert manifests, "At least one dataset manifest is required"
    assert {path.name.removesuffix(".manifest.json") for path in manifests} == {
        path.stem for path in caches
    }

    for path in manifests:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        source_url = manifest.get("source_url") or manifest.get("page_url")

        assert manifest["license"] == "CC BY 4.0", path
        assert manifest["license_url"] == CC_BY_4, path
        assert manifest["terms_url"] in PORTAL_TERMS, path
        assert manifest["terms_read_date"] == "2026-08-25", path
        assert source_url.startswith("https://"), path
        assert manifest["title"] in manifest["attribution"], path
        assert manifest["publisher"] in manifest["attribution"], path
        assert manifest["changes"].strip(), path


def test_every_bundled_font_family_has_its_ofl_text() -> None:
    font_files = sorted(FONT_DIR.glob("*.woff2"))
    licence_files = sorted(FONT_DIR.glob("LICENSE-*.txt"))

    assert font_files, "At least one bundled typeface is required"
    assert licence_files, "Bundled typefaces require their licence texts"

    family_prefixes = {
        path.name.removeprefix("LICENSE-").removesuffix(".txt") for path in licence_files
    }
    for font_path in font_files:
        assert any(font_path.name.startswith(f"{prefix}-") for prefix in family_prefixes), font_path

    for licence_path in licence_files:
        text = licence_path.read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE Version 1.1" in text, licence_path


def test_project_notice_points_to_separate_third_party_terms() -> None:
    notice = (REPO_ROOT / "NOTICE").read_text(encoding="utf-8")
    third_party = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert "THIRD_PARTY_NOTICES.md" in notice
    assert "Creative Commons Attribution 4.0" in third_party
    assert "SIL Open Font License 1.1" in third_party
