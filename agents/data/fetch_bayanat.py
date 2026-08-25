#!/usr/bin/env python3
"""BAYAN Bayanat HTML fetcher.

Bayanat.ae is the UAE federal open data portal. Dataset pages are served
as complete HTML to unauthenticated clients (HTTP 200, no token required).
The documented REST endpoint
  /api/DatasetResources/GetDatasetResource?resourceID={ResourceGUID}
was investigated thoroughly and found to be inaccessible:

  - Calling it with any value returns HTTP 400 or a zero-byte body.
  - The portal page markup contains two identifier schemes: Sitecore item
    GUIDs (used as page component identifiers, rejected by the endpoint)
    and base64url tokens in data-resource-id attributes (used for view
    counting, also rejected by GetDatasetResource).
  - The Resource GUID required by the endpoint is not exposed in the page
    HTML at all; it appears to be an internal portal concept not surfaced
    to unauthenticated clients.

The path that works is simpler: the dataset info page carries the Data
Explorer table in a full server-side render inside the page HTML. One
unauthenticated GET of the dataset info URL returns the complete preview
table with all column headers and up to five rows per resource.

Access method (deliberate design decision):
  GET https://bayanat.ae/en/Datasets/Dataset-info?id={token}
  Token: 43-character base64url string from the listing page hrefs.
  No authentication. No cookies. No antiforgery token.

Risk and mitigation:
  Parsing rendered HTML is more brittle than calling a stable API. The
  portal can change its markup at any time, breaking the column parse.
  Mitigation: the parser validates expected column names explicitly. If
  the expected columns are absent or the row count is zero, the script
  fails loudly (PARSE_FAILED or COLUMN_MISMATCH) rather than caching an
  empty or garbage table. The committed cache means a markup change breaks
  the refresh check visibly, not the demonstration.

This module exports one public function: check_bayanat_dataset().
"""

from __future__ import annotations

import hashlib
import html as html_module
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

TIMEOUT_SECONDS = 30
MIN_PAGE_BYTES = 10_000  # A valid dataset page is several hundred KB

# Table id pattern in the Bayanat HTML.
_TABLE_ID_RE = re.compile(r'id="accordionTableOne-(\d+)"')
_TH_RE = re.compile(r"<th>(.*?)</th>", re.DOTALL)
_TR_RE = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
_TD_SPAN_RE = re.compile(r"<td><span>(.*?)</span></td>", re.DOTALL)
_TOTAL_COUNT_RE = re.compile(r'"TotalCount":(\d+)')


class BayanatResult:
    OK = "OK"
    FETCH_FAILED = "FETCH_FAILED"
    PARSE_FAILED = "PARSE_FAILED"
    COLUMN_MISMATCH = "COLUMN_MISMATCH"
    CACHE_MISSING = "CACHE_MISSING"
    HASH_MISMATCH = "HASH_MISMATCH"
    OFFLINE_OK = "OFFLINE_OK"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_page(url: str) -> bytes:
    """Fetch a Bayanat dataset info page. Returns raw bytes."""
    req = urllib.request.Request(url, headers={"Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return resp.read()


def parse_tables(
    html_text: str,
    expected_columns: list[str],
) -> tuple[list[dict], list[int]]:
    """Parse all Data Explorer tables from the page HTML.

    Returns (table_list, total_counts_list). Each entry in table_list is a
    dict with keys 'columns' (list of str) and 'rows' (list of list of str).

    Fails loudly (raises ValueError) if the expected columns are not found
    in the first table, or if any table has zero rows.
    """
    table_indices = [int(m.group(1)) for m in _TABLE_ID_RE.finditer(html_text)]
    if not table_indices:
        raise ValueError(
            "No Data Explorer tables found in the page. "
            "The portal markup may have changed. "
            'Expected pattern: id="accordionTableOne-N".'
        )

    # Extract TotalCount values from the embedded JSON blobs.
    # Each resource contributes two occurrences (one in the data object and one
    # in PagingDTO). We deduplicate by taking every other value.
    all_tc = [int(m.group(1)) for m in _TOTAL_COUNT_RE.finditer(html_text)]
    # Use every second occurrence (the PagingDTO ones mirror the data ones).
    total_counts = all_tc[::2] if len(all_tc) >= len(table_indices) else all_tc

    tables = []
    for i in table_indices:
        marker = f'id="accordionTableOne-{i}"'
        marker_pos = html_text.find(marker)
        t_start = html_text.rfind("<table", 0, marker_pos)
        t_end = html_text.find("</table>", t_start) + len("</table>")
        table_html = html_text[t_start:t_end]

        headers = [
            html_module.unescape(h.strip())
            for h in _TH_RE.findall(table_html)
        ]
        rows = []
        for tr_content in _TR_RE.findall(table_html):
            cells = [
                html_module.unescape(c.strip())
                for c in _TD_SPAN_RE.findall(tr_content)
            ]
            if cells:
                rows.append(cells)

        tables.append({"columns": headers, "rows": rows})

    # Validate: first table must have the expected columns.
    if tables:
        found_cols = tables[0]["columns"]
        missing = [c for c in expected_columns if c not in found_cols]
        if missing:
            raise ValueError(
                f"Column mismatch. Expected: {expected_columns}. "
                f"Found: {found_cols}. "
                f"Missing: {missing}. "
                f"The portal markup may have changed."
            )

    # Validate: no table should be empty (a silent empty parse is worse than a
    # visible failure).
    for idx, t in enumerate(tables):
        if not t["rows"]:
            raise ValueError(
                f"Table {idx} has zero rows. "
                f"Columns found: {t['columns']}. "
                f"An empty table suggests the portal markup has changed "
                f"or the data is absent."
            )

    return tables, total_counts


def normalise_tables(tables: list[dict]) -> str:
    """Produce a canonical string for hash comparison.

    All rows from all tables are combined and sorted, so comparison is
    order-independent per row and resource-order-independent.
    """
    all_rows = []
    for t in tables:
        cols = t["columns"]
        for row_values in t["rows"]:
            record = dict(zip(cols, row_values))
            all_rows.append(json.dumps(record, sort_keys=True, ensure_ascii=False))
    return json.dumps(sorted(all_rows), ensure_ascii=False)


def check_bayanat_dataset(
    dataset_id: str,
    use_case_id: str,
    page_url: str,
    expected_columns: list[str],
    cache_dir: Path,
    offline: bool,
) -> tuple[str, str]:
    """Return (status, detail_string).

    Mirrors the interface of check_dataset() in fetch_datasets.py.
    """
    cache_path = cache_dir / f"{dataset_id}.json"

    if not cache_path.exists():
        return BayanatResult.CACHE_MISSING, f"cache file missing: {cache_path}"

    cache_hash = _sha256_file(cache_path)

    if offline:
        # Offline mode: compare the cache file SHA-256 against the hash recorded
        # in the manifest. A non-empty resources list is a necessary but not
        # sufficient check: an attacker can alter a row value and keep
        # len(resources) > 0. Only the manifest hash comparison catches that.
        # A missing manifest is treated as a failure for the same reason.
        manifest_path = cache_path.parent / (cache_path.stem + ".manifest.json")
        if not manifest_path.exists():
            return (
                BayanatResult.HASH_MISMATCH,
                f"manifest file missing: {manifest_path.name}. "
                f"Cannot verify cache integrity without a recorded hash. "
                f"Re-run in live mode to fetch and regenerate the manifest.",
            )
        try:
            manifest = json.loads(manifest_path.read_bytes())
        except json.JSONDecodeError as exc:
            return BayanatResult.HASH_MISMATCH, f"manifest file is not valid JSON: {exc}"
        manifest_hash = manifest.get("sha256_cache_file", "")
        if not manifest_hash:
            return (
                BayanatResult.HASH_MISMATCH,
                f"manifest does not record sha256_cache_file: {manifest_path.name}",
            )
        if cache_hash != manifest_hash:
            return (
                BayanatResult.HASH_MISMATCH,
                f"cache hash does not match manifest for {dataset_id}. "
                f"Manifest records: {manifest_hash[:16]}... "
                f"Actual file SHA-256: {cache_hash[:16]}... "
                f"The cache has been altered since it was committed. "
                f"Re-run in live mode to re-fetch and re-commit the authoritative data.",
            )
        # Manifest hash verified. Check internal consistency as a secondary guard.
        try:
            cache_doc = json.loads(cache_path.read_bytes())
            resources = cache_doc.get("resources", [])
            n_resources = len(resources)
            if n_resources == 0:
                return (
                    BayanatResult.HASH_MISMATCH,
                    "cache contains no resources",
                )
        except json.JSONDecodeError as exc:
            return BayanatResult.HASH_MISMATCH, f"cache file is not valid JSON: {exc}"
        return (
            BayanatResult.OFFLINE_OK,
            f"manifest hash verified: {cache_hash[:16]}... Resources: {n_resources}.",
        )

    # Live mode.
    try:
        raw_bytes = fetch_page(page_url)
    except urllib.error.URLError as exc:
        return (
            BayanatResult.FETCH_FAILED,
            f"network error fetching {page_url}: {exc}. "
            f"Offline cache SHA-256 {cache_hash[:16]}... was not used as a substitute. "
            f"The portal may be unreachable.",
        )
    except Exception as exc:  # noqa: BLE001
        return BayanatResult.FETCH_FAILED, f"unexpected error: {exc}"

    if len(raw_bytes) < MIN_PAGE_BYTES:
        return (
            BayanatResult.FETCH_FAILED,
            f"page response too small ({len(raw_bytes)} bytes). "
            f"Expected a full HTML page (> {MIN_PAGE_BYTES} bytes). "
            f"The portal may be redirecting or returning an error page.",
        )

    html_text = raw_bytes.decode("utf-8", errors="replace")

    try:
        live_tables, live_total_counts = parse_tables(html_text, expected_columns)
    except ValueError as exc:
        return BayanatResult.PARSE_FAILED, str(exc)

    live_norm = normalise_tables(live_tables)

    # Load committed cache for comparison.
    cache_doc = json.loads(cache_path.read_bytes())
    cache_resources = cache_doc.get("resources", [])
    cache_tables = [
        {"columns": r["columns"], "rows": r["rows"]}
        for r in cache_resources
    ]
    cache_norm = normalise_tables(cache_tables)

    live_hash = _sha256_bytes(live_norm.encode("utf-8"))
    cache_content_hash = _sha256_bytes(cache_norm.encode("utf-8"))

    total_preview_rows = sum(len(t["rows"]) for t in live_tables)
    n_resources = len(live_tables)
    first_tc = live_total_counts[0] if live_total_counts else "unknown"

    if live_hash != cache_content_hash:
        return (
            BayanatResult.HASH_MISMATCH,
            f"content mismatch for {dataset_id}. "
            f"Live normalised SHA-256: {live_hash[:16]}. "
            f"Cache normalised SHA-256: {cache_content_hash[:16]}. "
            f"Live preview: {n_resources} resources, {total_preview_rows} rows. "
            f"TotalCount (first resource): {first_tc}. "
            f"The portal page has changed since the cache was committed. "
            f"Re-run the fetch script to update the cache.",
        )

    return (
        BayanatResult.OK,
        f"live and cache agree. "
        f"{n_resources} resources, {total_preview_rows} preview rows. "
        f"Normalised content SHA-256: {live_hash[:16]}. "
        f"TotalCount per resource: {first_tc}.",
    )
