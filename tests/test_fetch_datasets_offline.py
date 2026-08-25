"""Offline cache-integrity tests for fetch_datasets.py and fetch_bayanat.py.

Finding L3 remediation. These are the attacker's tests.

Each test describes a concrete attack that the offline verifier must detect.
Run them against the unfixed code first: the first two parametrized cases will
FAIL, confirming the verifier accepted the attack. After the fix they must all
PASS.

Three scenarios per path (Ajman JSON and Bayanat HTML-parse):

  ALTERED   -- cache file has one value changed, internal consistency preserved
               (record count still matches metadata). Offline must return
               HASH_MISMATCH, not OFFLINE_OK.

  NO_MANIFEST -- manifest file deleted. Offline must return HASH_MISMATCH, not
               skip the check or report OFFLINE_OK.

  CLEAN     -- everything intact. Offline must return OFFLINE_OK.

No network calls are made. All fixtures are built from minimal valid structures
in a temporary directory.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


# Allow running from repo root.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.data.fetch_datasets import Result, check_dataset  # noqa: E402
from agents.data.fetch_bayanat import BayanatResult, check_bayanat_dataset  # noqa: E402


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_manifest(tmp: Path, dataset_id: str, cache_hash: str) -> None:
    manifest = {
        "dataset_id": dataset_id,
        "sha256_cache_file": cache_hash,
    }
    (tmp / f"{dataset_id}.manifest.json").write_bytes(
        json.dumps(manifest, indent=2).encode()
    )


# ---------------------------------------------------------------------------
# Ajman JSON-path fixtures
# ---------------------------------------------------------------------------

_AJMAN_DATASET_ID = "test-ajman-dataset"


def _make_ajman_cache(n_records: int = 3) -> bytes:
    """Return valid Ajman cache bytes with n_records records."""
    records = [{"id": i, "value": f"record_{i}"} for i in range(n_records)]
    doc = {
        "dataset_id": _AJMAN_DATASET_ID,
        "cached_records": n_records,
        "results": records,
    }
    return json.dumps(doc, indent=2).encode()


def _setup_ajman_clean(tmp: Path) -> None:
    """Write a valid Ajman cache + manifest."""
    cache_bytes = _make_ajman_cache()
    (tmp / f"{_AJMAN_DATASET_ID}.json").write_bytes(cache_bytes)
    _write_manifest(tmp, _AJMAN_DATASET_ID, _sha256_bytes(cache_bytes))


def _setup_ajman_altered(tmp: Path) -> None:
    """Write an Ajman cache that has been altered after the manifest was written.

    The attacker changes one record value but preserves cached_records == len(results),
    so the internal consistency check passes. Only a manifest hash comparison
    can catch this.
    """
    original_bytes = _make_ajman_cache()
    # Manifest records the original hash.
    _write_manifest(tmp, _AJMAN_DATASET_ID, _sha256_bytes(original_bytes))

    # Now alter the file on disk -- simulating tampering after manifest commit.
    doc = json.loads(original_bytes)
    doc["results"][0]["value"] = "ATTACKER_INJECTED"
    # cached_records still equals len(results): internal consistency preserved.
    assert doc["cached_records"] == len(doc["results"])
    altered_bytes = json.dumps(doc, indent=2).encode()
    assert altered_bytes != original_bytes, "altered bytes must differ from original"
    (tmp / f"{_AJMAN_DATASET_ID}.json").write_bytes(altered_bytes)


def _setup_ajman_no_manifest(tmp: Path) -> None:
    """Write a valid Ajman cache but no manifest."""
    (tmp / f"{_AJMAN_DATASET_ID}.json").write_bytes(_make_ajman_cache())
    # Deliberately no manifest file.


# ---------------------------------------------------------------------------
# Bayanat HTML-parse-path fixtures
# ---------------------------------------------------------------------------

_BAYANAT_DATASET_ID = "test-bayanat-dataset"
_BAYANAT_COLS = ["Year", "District_AR", "Value"]
_BAYANAT_URL = "https://example.invalid"  # Never fetched in offline mode.


def _make_bayanat_cache(resource_value: str = "original_value") -> bytes:
    """Return valid Bayanat cache bytes with one resource."""
    doc = {
        "dataset_id": _BAYANAT_DATASET_ID,
        "resources": [
            {
                "columns": _BAYANAT_COLS,
                "rows": [["2002", "Abu Dhabi", resource_value]],
                "total_count": 27,
            }
        ],
    }
    return json.dumps(doc, indent=2, ensure_ascii=False).encode()


def _setup_bayanat_clean(tmp: Path) -> None:
    cache_bytes = _make_bayanat_cache()
    (tmp / f"{_BAYANAT_DATASET_ID}.json").write_bytes(cache_bytes)
    _write_manifest(tmp, _BAYANAT_DATASET_ID, _sha256_bytes(cache_bytes))


def _setup_bayanat_altered(tmp: Path) -> None:
    """Alter the Bayanat cache after the manifest was written.

    resources list is non-empty (passes the old n_resources > 0 check).
    Only a hash comparison catches this.
    """
    original_bytes = _make_bayanat_cache()
    _write_manifest(tmp, _BAYANAT_DATASET_ID, _sha256_bytes(original_bytes))

    doc = json.loads(original_bytes)
    doc["resources"][0]["rows"][0][2] = "ATTACKER_INJECTED"
    # len(resources) is still 1 -- non-zero.
    altered_bytes = json.dumps(doc, indent=2, ensure_ascii=False).encode()
    assert altered_bytes != original_bytes
    (tmp / f"{_BAYANAT_DATASET_ID}.json").write_bytes(altered_bytes)


def _setup_bayanat_no_manifest(tmp: Path) -> None:
    (tmp / f"{_BAYANAT_DATASET_ID}.json").write_bytes(_make_bayanat_cache())
    # No manifest.


# ---------------------------------------------------------------------------
# Ajman tests
# ---------------------------------------------------------------------------

def test_ajman_offline_rejects_altered_cache(tmp_path: Path) -> None:
    """An altered but internally consistent Ajman cache must not pass offline.

    This is the attacker's test. Before the fix, check_dataset returned OFFLINE_OK
    for this case. After the fix it must return HASH_MISMATCH.
    """
    _setup_ajman_altered(tmp_path)
    status, detail = check_dataset(
        _AJMAN_DATASET_ID, "uc-test", None, offline=True, cache_dir=tmp_path
    )
    assert status == Result.HASH_MISMATCH, (
        f"Expected HASH_MISMATCH for altered cache, got {status!r}. "
        f"Detail: {detail}"
    )
    # The error message must name both hashes so the reviewer can act.
    assert "manifest" in detail.lower(), f"Detail should mention 'manifest': {detail}"


def test_ajman_offline_rejects_missing_manifest(tmp_path: Path) -> None:
    """Offline mode must fail if the manifest is absent.

    Before the fix, a missing manifest was not checked at all. The verifier
    proceeded without comparing anything. After the fix it must return
    HASH_MISMATCH rather than silently accepting the unverifiable cache.
    """
    _setup_ajman_no_manifest(tmp_path)
    status, detail = check_dataset(
        _AJMAN_DATASET_ID, "uc-test", None, offline=True, cache_dir=tmp_path
    )
    assert status == Result.HASH_MISMATCH, (
        f"Expected HASH_MISMATCH for missing manifest, got {status!r}. "
        f"Detail: {detail}"
    )
    assert "manifest" in detail.lower(), f"Detail should mention 'manifest': {detail}"


def test_ajman_offline_accepts_clean_cache(tmp_path: Path) -> None:
    """A clean, unaltered Ajman cache must pass offline verification."""
    _setup_ajman_clean(tmp_path)
    status, detail = check_dataset(
        _AJMAN_DATASET_ID, "uc-test", None, offline=True, cache_dir=tmp_path
    )
    assert status == Result.OFFLINE_OK, (
        f"Expected OFFLINE_OK for clean cache, got {status!r}. "
        f"Detail: {detail}"
    )


# ---------------------------------------------------------------------------
# Bayanat tests
# ---------------------------------------------------------------------------

def test_bayanat_offline_rejects_altered_cache(tmp_path: Path) -> None:
    """An altered but non-empty Bayanat cache must not pass offline.

    Before the fix, check_bayanat_dataset returned OFFLINE_OK when resources
    was non-empty, regardless of whether the hash matched the manifest.
    """
    _setup_bayanat_altered(tmp_path)
    status, detail = check_bayanat_dataset(
        _BAYANAT_DATASET_ID,
        "uc-test",
        _BAYANAT_URL,
        _BAYANAT_COLS,
        tmp_path,
        offline=True,
    )
    assert status == BayanatResult.HASH_MISMATCH, (
        f"Expected HASH_MISMATCH for altered Bayanat cache, got {status!r}. "
        f"Detail: {detail}"
    )
    assert "manifest" in detail.lower(), f"Detail should mention 'manifest': {detail}"


def test_bayanat_offline_rejects_missing_manifest(tmp_path: Path) -> None:
    """Offline Bayanat check must fail if the manifest is absent."""
    _setup_bayanat_no_manifest(tmp_path)
    status, detail = check_bayanat_dataset(
        _BAYANAT_DATASET_ID,
        "uc-test",
        _BAYANAT_URL,
        _BAYANAT_COLS,
        tmp_path,
        offline=True,
    )
    assert status == BayanatResult.HASH_MISMATCH, (
        f"Expected HASH_MISMATCH for missing manifest, got {status!r}. "
        f"Detail: {detail}"
    )
    assert "manifest" in detail.lower(), f"Detail should mention 'manifest': {detail}"


def test_bayanat_offline_accepts_clean_cache(tmp_path: Path) -> None:
    """A clean, unaltered Bayanat cache must pass offline verification."""
    _setup_bayanat_clean(tmp_path)
    status, detail = check_bayanat_dataset(
        _BAYANAT_DATASET_ID,
        "uc-test",
        _BAYANAT_URL,
        _BAYANAT_COLS,
        tmp_path,
        offline=True,
    )
    assert status == BayanatResult.OFFLINE_OK, (
        f"Expected OFFLINE_OK for clean Bayanat cache, got {status!r}. "
        f"Detail: {detail}"
    )
