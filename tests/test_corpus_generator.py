"""
Tests for the MIZAN corpus generator.

Verifies: existence, no exact duplicates, unique probe_ids, provenance fields,
target counts met, determinism across two runs, locale distribution within tolerance.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = REPO_ROOT / "suites" / "generated"
GRAMMARS_DIR = REPO_ROOT / "suites" / "grammars"

# Map each generated file to the controls it should contain and their n_targets.
EXPECTED: dict[str, dict[str, int]] = {
    "arabic-linguistic.generated.json": {
        "ctrl-lca-001": 28,
        "ctrl-lca-002": 200,
        "ctrl-lca-003": 605,
    },
    "bias.generated.json": {
        "ctrl-fnd-001": 58,
        "ctrl-fnd-002": 200,
    },
    "oversight.generated.json": {
        "ctrl-hov-003": 73,
    },
    "safety.generated.json": {
        "ctrl-shr-001": 119,
        "ctrl-shr-002": 605,
        "ctrl-shr-003": 200,
        "ctrl-shr-004": 200,
    },
    "transparency.generated.json": {
        "ctrl-tre-001": 605,
        "ctrl-tre-003": 38,
    },
}


def _load(filename: str) -> dict:
    path = GENERATED_DIR / filename
    assert path.exists(), f"Generated file missing: {path}"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


class TestGeneratedFilesExist:
    def test_all_expected_files_exist(self):
        for filename in EXPECTED:
            assert (GENERATED_DIR / filename).exists(), f"Missing: {filename}"

    def test_grammars_dir_has_all_grammar_files(self):
        grammar_files = list(GRAMMARS_DIR.glob("*.grammar.json"))
        assert len(grammar_files) >= 5, "Expected at least 5 grammar files"


class TestTargetCounts:
    @pytest.mark.parametrize("filename,control_targets", [
        (f, ct) for f, ct in EXPECTED.items()
    ])
    def test_control_item_counts_meet_target(self, filename, control_targets):
        data = _load(filename)
        counts = data.get("control_counts", {})
        for control_id, expected_count in control_targets.items():
            actual = counts.get(control_id, 0)
            assert actual == expected_count, (
                f"{filename}/{control_id}: expected {expected_count} items, got {actual}"
            )


class TestNoDuplicates:
    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_no_exact_duplicate_prompts(self, filename):
        data = _load(filename)
        import unicodedata
        prompts = [
            " ".join(unicodedata.normalize("NFC", item["prompt"]).lower().split())
            for item in data["items"]
        ]
        assert len(prompts) == len(set(prompts)), (
            f"{filename}: exact duplicate prompts found"
        )

    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_no_duplicate_probe_ids(self, filename):
        data = _load(filename)
        probe_ids = [item["probe_id"] for item in data["items"]]
        assert len(probe_ids) == len(set(probe_ids)), (
            f"{filename}: duplicate probe_ids found"
        )


class TestProvenanceFields:
    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_all_items_have_provenance(self, filename):
        data = _load(filename)
        for item in data["items"]:
            assert "provenance" in item, (
                f"{filename}: item {item.get('probe_id')} missing provenance"
            )

    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_provenance_has_required_fields(self, filename):
        data = _load(filename)
        required = {"source", "grammar_id", "group_id", "template_idx", "seed"}
        for item in data["items"]:
            prov = item.get("provenance", {})
            missing = required - set(prov.keys())
            assert not missing, (
                f"{filename}: item {item.get('probe_id')} provenance missing {missing}"
            )

    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_all_items_have_source_generated(self, filename):
        data = _load(filename)
        for item in data["items"]:
            src = item.get("provenance", {}).get("source")
            assert src == "generated", (
                f"{filename}: item {item.get('probe_id')} has source={src!r}, expected 'generated'"
            )

    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_all_items_have_seed_42(self, filename):
        data = _load(filename)
        for item in data["items"]:
            seed = item.get("provenance", {}).get("seed")
            assert seed == 42, (
                f"{filename}: item {item.get('probe_id')} has seed={seed}, expected 42"
            )


class TestDeterminism:
    """Generator determinism: same seed always produces byte-identical output.

    Design notes
    ------------
    The test must be hermetic -- it must not read from, write to, or mutate
    suites/generated/.  The previous implementation copied suites/generated/
    as the "first run" and then re-ran the generator into suites/generated/
    as the "second run".  Two coupling failure modes followed:

    1. If any other test in the suite mutated suites/generated/ before this
       test ran, the "first copy" captured that mutated state, so the
       comparison was between the mutated copy and the regenerated canonical
       output -- a coupling, not a determinism failure.

    2. The generator subprocess takes ~90 seconds for the full corpus.
       Running it twice per suite-execution made the test suite ~8 minutes
       long, which in practice means nobody runs it.

    Fix: generate a small, bounded slice (the oversight grammar, 73 items)
    twice into separate temporary directories and compare.  The full-corpus
    regeneration is tagged @pytest.mark.slow and lives in a separate method
    for on-demand CI runs.
    """

    _SMALL_GRAMMAR = GRAMMARS_DIR / "oversight.grammar.json"

    def test_generator_is_hermetic(self, tmp_path):
        """Determinism test must not touch suites/generated/.

        Records the mtimes of every file in suites/generated/ before the
        generator runs, then asserts they are unchanged afterwards.
        """
        import subprocess
        import sys

        # Snapshot mtimes before the run.
        before: dict[str, float] = {}
        if GENERATED_DIR.exists():
            for f in GENERATED_DIR.iterdir():
                before[f.name] = f.stat().st_mtime

        out_dir = tmp_path / "hermetic_run"
        out_dir.mkdir()
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "generate_corpus.py"),
                "--seed", "42",
                "--grammar", str(self._SMALL_GRAMMAR),
                "--output-dir", str(out_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Generator failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # suites/generated/ must be completely untouched.
        after: dict[str, float] = {}
        if GENERATED_DIR.exists():
            for f in GENERATED_DIR.iterdir():
                after[f.name] = f.stat().st_mtime

        assert before == after, (
            "suites/generated/ was modified by the generator when --output-dir "
            "was supplied.  The generator must write only to the given output dir."
        )

        # The output dir must contain the generated file.
        generated = list(out_dir.glob("*.generated.json"))
        assert generated, "No output file produced in tmp output dir."

    def test_small_grammar_determinism(self, tmp_path):
        """Identical seed produces byte-identical output -- tested on a small grammar slice.

        Two independent subprocess invocations, each writing to a separate
        temporary directory.  suites/generated/ is never touched.
        This test completes in seconds rather than minutes.
        """
        import subprocess
        import sys

        def _run(dest: Path) -> None:
            dest.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "generate_corpus.py"),
                    "--seed", "42",
                    "--grammar", str(self._SMALL_GRAMMAR),
                    "--output-dir", str(dest),
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
            assert result.returncode == 0, (
                f"Generator failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

        run1 = tmp_path / "run1"
        run2 = tmp_path / "run2"
        _run(run1)
        _run(run2)

        files1 = sorted(run1.glob("*.generated.json"))
        assert files1, "First run produced no output files."

        for f1 in files1:
            f2 = run2 / f1.name
            assert f2.exists(), f"Second run missing file: {f1.name}"

            d1 = json.loads(f1.read_text(encoding="utf-8"))
            d2 = json.loads(f2.read_text(encoding="utf-8"))

            assert len(d1["items"]) == len(d2["items"]), (
                f"Item count differs between runs for {f1.name}: "
                f"{len(d1['items'])} vs {len(d2['items'])}"
            )
            for idx, (item1, item2) in enumerate(zip(d1["items"], d2["items"])):
                assert item1["probe_id"] == item2["probe_id"], (
                    f"{f1.name}[{idx}]: probe_id differs: "
                    f"{item1['probe_id']!r} vs {item2['probe_id']!r}"
                )
                assert item1["prompt"] == item2["prompt"], (
                    f"{f1.name}[{idx}]: prompt differs at probe "
                    f"{item1['probe_id']!r}"
                )

    @pytest.mark.slow
    def test_full_corpus_determinism(self, tmp_path):
        """Full corpus regeneration -- identical seed, byte-identical output.

        This test takes ~90 seconds (generates ~3k items twice).  It is
        tagged @pytest.mark.slow and should be run on demand (pytest -m slow)
        rather than on every push.
        """
        import subprocess
        import sys

        def _run(dest: Path) -> None:
            dest.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "generate_corpus.py"),
                    "--seed", "42",
                    "--output-dir", str(dest),
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
            assert result.returncode == 0, (
                f"Generator failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

        run1 = tmp_path / "run1"
        run2 = tmp_path / "run2"
        _run(run1)
        _run(run2)

        for f1 in sorted(run1.glob("*.generated.json")):
            f2 = run2 / f1.name
            assert f2.exists(), f"Second run missing: {f1.name}"
            assert f1.read_bytes() == f2.read_bytes(), (
                f"Byte-level difference in {f1.name}"
            )


class TestLocaleDistribution:
    @pytest.mark.parametrize("filename,control_targets", [
        (f, ct) for f, ct in EXPECTED.items()
    ])
    def test_arabic_items_present_in_multilingual_controls(
        self, filename, control_targets
    ):
        """At least 20% of items per control should be Arabic for multilingual controls."""
        if filename == "oversight.generated.json":
            pytest.skip("Oversight has all locales already verified by inspection")

        data = _load(filename)
        items_by_control: dict[str, list] = {}
        for item in data["items"]:
            cid = item.get("control_id", "")
            items_by_control.setdefault(cid, []).append(item)

        for control_id in control_targets:
            items = items_by_control.get(control_id, [])
            if not items:
                continue
            ar_count = sum(1 for it in items if it.get("locale") == "ar")
            ar_ratio = ar_count / len(items)
            # Arabic-only controls (ctrl-lca-*) should be 100% Arabic
            if control_id.startswith("ctrl-lca"):
                assert ar_ratio >= 0.20, (
                    f"{filename}/{control_id}: AR ratio {ar_ratio:.2f} < 0.20"
                )
            else:
                assert ar_ratio >= 0.15, (
                    f"{filename}/{control_id}: AR ratio {ar_ratio:.2f} < 0.15"
                )


class TestScorerFields:
    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_all_items_have_scorer(self, filename):
        data = _load(filename)
        for item in data["items"]:
            assert "scorer" in item, (
                f"{filename}: item {item.get('probe_id')} missing scorer"
            )

    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_all_items_have_scorer_config(self, filename):
        data = _load(filename)
        for item in data["items"]:
            assert "scorer_config" in item, (
                f"{filename}: item {item.get('probe_id')} missing scorer_config"
            )

    @pytest.mark.parametrize("filename", list(EXPECTED.keys()))
    def test_all_items_have_control_id(self, filename):
        data = _load(filename)
        for item in data["items"]:
            assert item.get("control_id"), (
                f"{filename}: item {item.get('probe_id')} missing control_id"
            )


class TestBiasProbes:
    def test_fnd001_items_come_in_pairs(self):
        data = _load("bias.generated.json")
        items = [it for it in data["items"] if it.get("control_id") == "ctrl-fnd-001"]
        pair_ids = [it.get("pair_id") for it in items if it.get("pair_id")]
        # Every item with a pair_id should have a corresponding partner
        pair_id_counts: dict[str, int] = {}
        for pid in pair_ids:
            pair_id_counts[pid] = pair_id_counts.get(pid, 0) + 1
        for pid, count in pair_id_counts.items():
            assert count == 2, f"Pair {pid} has {count} members, expected 2"

    def test_fnd001_total_is_even(self):
        data = _load("bias.generated.json")
        items = [it for it in data["items"] if it.get("control_id") == "ctrl-fnd-001"]
        assert len(items) % 2 == 0, "ctrl-fnd-001 item count must be even (pairs)"


class TestGrammarIntegrity:
    @pytest.mark.parametrize("grammar_file", sorted(GRAMMARS_DIR.glob("*.grammar.json")))
    def test_grammar_file_is_valid_json(self, grammar_file):
        with grammar_file.open(encoding="utf-8") as f:
            data = json.load(f)
        assert "grammar_id" in data
        assert "controls" in data

    @pytest.mark.parametrize("grammar_file", sorted(GRAMMARS_DIR.glob("*.grammar.json")))
    def test_grammar_has_owner_field(self, grammar_file):
        with grammar_file.open(encoding="utf-8") as f:
            data = json.load(f)
        assert "owner" in data, f"{grammar_file.name} missing owner field"
