"""Dataset bindings: which government dataset grounds which use case.

Every entry is read from the manifest a fetch wrote next to the cached
dataset in suites/data/. Nothing here is typed by hand: the publishing
entity, the portal, the resource identifier, the read date and the cache
hash all come from the manifest, so the interface cannot show an entity or a
dataset that no fetch ever verified.

The binding table itself (which dataset grounds which use case) is the same
table the fetch script drives from, recorded in
docs/evidence/data_sources.md.

British English throughout.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "suites" / "data"

# dataset_id -> use_case_id, matching agents/data/fetch_datasets.py.
# speed-center-services-names-and-fees is retained in the cache as a
# reference binding and is deliberately bound to no use case; see
# docs/evidence/data_sources.md.
_BINDINGS: dict[str, str] = {
    "bayanat-population-sex-district":                 "uc-001",
    "byanat-alanzmh-walsyasat-bdaerh-almward-albshryh": "uc-002",
    "benefit-certificates-for-rent-contracts":         "uc-003",
    "number-of-reports-security-certificates-and-initiatives-of-al-hamidiya-comprehen": "uc-004",
    "coo-re-export-2023-part-2":                       "uc-005",
}

# The portal each publishing entity publishes through, used for attribution
# in the interface. Recorded in docs/evidence/data_sources.md.
_PORTAL_URLS: dict[str, str] = {
    "bayanat.ae": "https://bayanat.ae",
    "Ajman Open Data Portal (data.ajman.ae)": "https://data.ajman.ae",
}


@lru_cache(maxsize=1)
def dataset_bindings() -> list[dict[str, Any]]:
    """Return one record per bound dataset, read from its manifest."""
    out: list[dict[str, Any]] = []
    for dataset_id, use_case_id in _BINDINGS.items():
        manifest_path = _DATA_DIR / f"{dataset_id}.manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        portal = manifest.get("portal", "")
        out.append({
            "use_case_id":     use_case_id,
            "dataset_id":      dataset_id,
            "title":           manifest.get("title", dataset_id),
            "publisher":       manifest.get("publisher", ""),
            "portal":          portal,
            "portal_url":      _PORTAL_URLS.get(portal, ""),
            "page_url":        manifest.get("page_url") or "",
            "resource_guid":   manifest.get("dataset_uid", ""),
            "read_date":       manifest.get("read_date", ""),
            "last_modified":   manifest.get("modified", ""),
            "cache_sha256":    manifest.get("sha256_cache_file", ""),
        })
    out.sort(key=lambda r: r["use_case_id"])
    return out


def bindings_for(use_case_id: str) -> list[dict[str, Any]]:
    """Return the dataset bindings that ground one use case."""
    return [b for b in dataset_bindings() if b["use_case_id"] == use_case_id]
