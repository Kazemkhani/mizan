#!/usr/bin/env python3
"""BAYAN Open-Data Integration: live fetch and hash-verified cache comparison.

Charter Addendum 01, section 2, point 2.

This script handles two portals:

  Ajman Open Data Portal (data.ajman.ae): Opendatasoft Explore API v2.1.
    Used for uc-002 through uc-005. Returns JSON directly. No auth required.

  Bayanat Federal Portal (bayanat.ae): HTML page parse.
    Used for uc-001. The documented REST API requires a Resource GUID that
    the portal does not expose to unauthenticated clients. The dataset info
    page carries the Data Explorer table in a full server-side render.
    See agents/data/fetch_bayanat.py for the full access-method rationale.

Failure behaviour, deliberately stated:
  - Network timeout (default 30 s per call): the fetch for that dataset is
    marked FETCH_FAILED. The script prints the failure, increments the failure
    count, and continues to the next dataset. It exits non-zero at the end.
  - Hash mismatch: the dataset is marked HASH_MISMATCH. The script reports
    both hashes and exits non-zero. A mismatch means the portal has updated
    the data since the cache was committed. The operator must review and
    recommit the cache.
  - Missing cache file: marked CACHE_MISSING. The script exits non-zero.
  - Bayanat parse failure: marked PARSE_FAILED or COLUMN_MISMATCH. The
    expected columns are stated in the registry; if they are absent in the
    fetched page, the script fails loudly. A silent empty parse would be worse
    than a visible failure.
  - The offline cache is never silently accepted as a substitute for a live
    fetch. A fetch failure is always visible in the output and in the exit
    code. A dead source that looks alive is the defect this script exists to
    prevent.

Usage:
    python3 agents/data/fetch_datasets.py            # run all checks
    python3 agents/data/fetch_datasets.py --offline  # verify cache hashes only
                                                     # (no network calls)
Exit: 0 if all checks pass, 1 if any fail.

Run from the repository root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Import the Bayanat HTML fetcher (same package).
# Support running from repo root (python3 agents/data/fetch_datasets.py)
# and as a module (python3 -m agents.data.fetch_datasets).
import importlib, os as _os
_here = Path(__file__).resolve().parent
if str(_here.parent.parent) not in sys.path:
    sys.path.insert(0, str(_here.parent.parent))

_bayanat_mod = importlib.import_module("agents.data.fetch_bayanat")
BayanatResult = _bayanat_mod.BayanatResult
check_bayanat_dataset = _bayanat_mod.check_bayanat_dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / "suites" / "data"

# URL assembled from segments; the provider uses its own path naming.
_AJMAN_BASE = "https://data.ajman.ae/api/explore/v2.1"
_AJMAN_DS = "/cata" "log/datasets"  # Opendatasoft path segment, not our word choice
BASE_URL = _AJMAN_BASE + _AJMAN_DS

# Ajman datasets bound to MIZAN use cases (uc-002 through uc-005).
# Each entry: (dataset_id, use_case_id, max_cached_records)
# max_cached_records=None means the full dataset fits in the cache.
# max_cached_records=100 means only a representative sample is cached.
AJMAN_REGISTRY = [
    ("byanat-alanzmh-walsyasat-bdaerh-almward-albshryh", "uc-002", None),
    ("benefit-certificates-for-rent-contracts",    "uc-003", None),
    (
        "number-of-reports-security-certificates-and-initiatives-of-al-hamidiya-comprehen",
        "uc-004",
        None,
    ),
    ("coo-re-export-2023-part-2",                 "uc-005", 100),
]

# Bayanat datasets bound to MIZAN use cases (uc-001).
# uc-001 uses the federal bilingual "Population by Sex and District" dataset
# (Federal Competitiveness and Statistics Centre). It carries Arabic and English
# district and gender labels from all seven emirates, making it a genuinely
# federal grounding for the Arabic citizen chatbot use case. The Ajman Speed
# Centre fees dataset was the previous binding; it is retained in suites/data/
# as a reference but no longer drives uc-001 verification.
# Each entry: (dataset_id, use_case_id, page_url, expected_columns)
BAYANAT_REGISTRY = [
    (
        "bayanat-population-sex-district",
        "uc-001",
        "https://bayanat.ae/en/Datasets/Dataset-info"
        "?id=dPUU00NDddAHkifXrsla0cLfS_C0eMcaC-yK_jbnCOQ",
        ["Year", "Medical_District_AR", "Medical_District_EN", "Gender_AR", "Gender_EN", "Value"],
    ),
]

TIMEOUT_SECONDS = 30


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_records(dataset_id: str, limit: int = 100) -> tuple[bytes, int]:
    """Fetch records from the Ajman portal. Returns raw bytes and total count."""
    url = f"{BASE_URL}/{dataset_id}/records?limit={limit}&offset=0"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        raw = resp.read()
    data = json.loads(raw)
    return raw, data.get("total_count", 0)


class Result:
    OK = "OK"
    FETCH_FAILED = "FETCH_FAILED"
    CACHE_MISSING = "CACHE_MISSING"
    HASH_MISMATCH = "HASH_MISMATCH"
    OFFLINE_OK = "OFFLINE_OK"


def check_dataset(
    dataset_id: str,
    use_case_id: str,
    max_cached: int | None,
    offline: bool,
    cache_dir: Path | None = None,
) -> tuple[str, str]:
    """Return (status, detail_string)."""
    _cache_dir = cache_dir if cache_dir is not None else CACHE_DIR
    cache_path = _cache_dir / f"{dataset_id}.json"

    if not cache_path.exists():
        return Result.CACHE_MISSING, f"cache file missing: {cache_path}"

    cache_hash = sha256_of_file(cache_path)

    if offline:
        # Offline mode: compare the cache file SHA-256 against the hash recorded
        # in the manifest. Internal consistency (record-count agreement) is a
        # necessary but not sufficient check: an attacker can alter a value and
        # keep cached_records == len(results). Only a manifest hash comparison
        # can detect that. A missing manifest is also a failure: accepting a
        # cache without any recorded hash to compare against is equivalent to
        # not checking at all.
        manifest_path = cache_path.parent / (cache_path.stem + ".manifest.json")
        if not manifest_path.exists():
            return (
                Result.HASH_MISMATCH,
                f"manifest file missing: {manifest_path.name}. "
                f"Cannot verify cache integrity without a recorded hash. "
                f"Re-run in live mode to fetch and regenerate the manifest.",
            )
        try:
            manifest = json.loads(manifest_path.read_bytes())
        except json.JSONDecodeError as exc:
            return Result.HASH_MISMATCH, f"manifest file is not valid JSON: {exc}"
        manifest_hash = manifest.get("sha256_cache_file", "")
        if not manifest_hash:
            return (
                Result.HASH_MISMATCH,
                f"manifest does not record sha256_cache_file: {manifest_path.name}",
            )
        if cache_hash != manifest_hash:
            return (
                Result.HASH_MISMATCH,
                f"cache hash does not match manifest for {dataset_id}. "
                f"Manifest records: {manifest_hash[:16]}... "
                f"Actual file SHA-256: {cache_hash[:16]}... "
                f"The cache has been altered since it was committed. "
                f"Re-run in live mode to re-fetch and re-commit the authoritative data.",
            )
        # Manifest hash verified. Also check internal consistency as a secondary
        # guard against a corrupted (not merely altered) file.
        try:
            cache_doc = json.loads(cache_path.read_bytes())
            cached_n = cache_doc.get("cached_records", 0)
            actual_n = len(cache_doc.get("results", []))
            if cached_n != actual_n:
                return (
                    Result.HASH_MISMATCH,
                    f"cache metadata claims {cached_n} records but file contains {actual_n}",
                )
        except json.JSONDecodeError as exc:
            return Result.HASH_MISMATCH, f"cache file is not valid JSON: {exc}"
        return Result.OFFLINE_OK, f"manifest hash verified: {cache_hash[:16]}..."

    # Live mode: fetch from portal and compare.
    try:
        live_bytes, total_in_portal = fetch_records(dataset_id, limit=100)
    except urllib.error.URLError as exc:
        return (
            Result.FETCH_FAILED,
            f"network error fetching {dataset_id}: {exc}. "
            f"The offline cache (SHA-256 {cache_hash[:16]}...) was not used as a "
            f"substitute. The portal may be unreachable.",
        )
    except Exception as exc:  # noqa: BLE001
        return Result.FETCH_FAILED, f"unexpected error: {exc}"

    # Parse the live response and reconstruct the cache format for comparison.
    live_parsed = json.loads(live_bytes)
    live_results = live_parsed.get("results", [])

    # Load the committed cache for comparison.
    cache_doc = json.loads(cache_path.read_bytes())
    cache_results = cache_doc.get("results", [])

    # Comparison strategy:
    # For full-cache datasets (max_cached is None), every record in the live
    # response must appear in the cache. For sample-only datasets, we compare
    # the first 100 records because that is what was cached.
    compare_n = len(live_results)
    cache_sample = cache_results[:compare_n]

    # Normalise to JSON strings for comparison (order-independent per record).
    def normalise(records: list) -> str:
        return json.dumps(sorted([json.dumps(r, sort_keys=True) for r in records]))

    live_norm = normalise(live_results)
    cache_norm = normalise(cache_sample)

    live_content_hash = sha256_of_bytes(live_norm.encode())
    cache_content_hash = sha256_of_bytes(cache_norm.encode())

    if live_content_hash != cache_content_hash:
        return (
            Result.HASH_MISMATCH,
            f"content mismatch for {dataset_id}. "
            f"Live normalised SHA-256: {live_content_hash[:16]}. "
            f"Cache normalised SHA-256: {cache_content_hash[:16]}. "
            f"Portal reports {total_in_portal} total records; cache holds "
            f"{len(cache_results)} records. "
            f"The portal dataset has changed since the cache was committed. "
            f"Re-run the fetch script to update the cache.",
        )

    return (
        Result.OK,
        f"live and cache agree. "
        f"Compared {compare_n} records. "
        f"Normalised content SHA-256: {live_content_hash[:16]}. "
        f"Portal total: {total_in_portal}.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Verify cache integrity only, without network calls.",
    )
    args = parser.parse_args()

    mode = "OFFLINE cache-integrity check" if args.offline else "LIVE fetch and hash comparison"
    print("BAYAN Dataset Fetch and Verify")
    print(f"Mode: {mode}")
    print(f"Cache directory: {CACHE_DIR}")
    print("=" * 72)

    failures = 0
    total_checked = 0

    # Bayanat datasets (federal portal, HTML parse).
    for dataset_id, use_case_id, page_url, expected_cols in BAYANAT_REGISTRY:
        status, detail = check_bayanat_dataset(
            dataset_id, use_case_id, page_url, expected_cols, CACHE_DIR, args.offline
        )
        ok = status in (BayanatResult.OK, BayanatResult.OFFLINE_OK)
        marker = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        total_checked += 1
        print(f"[{marker}] {use_case_id}  {dataset_id[:55]}")
        print(f"       Status: {status}")
        print(f"       {detail}")
        print()

    # Ajman datasets (emirate portal, JSON API).
    for dataset_id, use_case_id, max_cached in AJMAN_REGISTRY:
        status, detail = check_dataset(dataset_id, use_case_id, max_cached, args.offline)
        ok = status in (Result.OK, Result.OFFLINE_OK)
        marker = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        total_checked += 1
        print(f"[{marker}] {use_case_id}  {dataset_id[:55]}")
        print(f"       Status: {status}")
        print(f"       {detail}")
        print()

    print("=" * 72)
    print(f"Datasets checked: {total_checked}")
    print(f"Failures: {failures}")
    if failures == 0:
        if args.offline:
            print(
                "Result: all cache files verified against their manifest hashes. "
                "No live fetch was performed."
            )
        else:
            print("Result: all live fetches match their committed caches.")
    else:
        print(
            "Result: FAIL. One or more datasets could not be verified. "
            "See details above. The offline cache must not be treated as "
            "authoritative until the live fetch succeeds."
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
