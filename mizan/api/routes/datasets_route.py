"""Government dataset binding routes.

GET /api/v1/datasets   -- every dataset binding, with its publishing entity

The interface uses this to show which government entities' published data
grounds the evaluation, with the resource identifier, the read date and the
cache hash a reader can check against docs/evidence/data_sources.md.

British English throughout.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from mizan.api import bindings

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", summary="List every government dataset binding")
async def list_datasets() -> list[dict[str, Any]]:
    """Return all dataset bindings, read from the fetch manifests."""
    return bindings.dataset_bindings()
