"""Tests for the API health endpoint and package importability.

Wave 0 acceptance criteria verified here:
  - `import mizan` works.
  - The FastAPI application starts and responds to GET /api/v1/health.
  - The health response conforms to the HealthOut schema.
  - The database connectivity check returns a valid status string.
"""

from __future__ import annotations

import pytest
import mizan
from httpx import AsyncClient, ASGITransport

from mizan.api.main import app
from mizan.api.schemas import HealthOut


def test_package_importable() -> None:
    """The mizan package must be importable and expose __version__."""
    assert hasattr(mizan, "__version__")
    assert isinstance(mizan.__version__, str)
    assert len(mizan.__version__) > 0


@pytest.mark.asyncio
async def test_health_endpoint_returns_200() -> None:
    """GET /api/v1/health must return HTTP 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_schema() -> None:
    """GET /api/v1/health must return a valid HealthOut payload."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")

    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == mizan.__version__
    assert data["database"] in ("ok", "error")


@pytest.mark.asyncio
async def test_use_cases_list_returns_five() -> None:
    """GET /api/v1/use-cases must return the five government use cases."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/use-cases")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


@pytest.mark.asyncio
async def test_model_registration_round_trip() -> None:
    """POST /api/v1/models followed by GET /api/v1/models/{id} must return the same record."""
    payload = {
        "name_en": "Test Model",
        "name_ar": "نموذج اختبار",
        "provider": "Test Provider",
        "version": "1.0.0",
        "endpoint_url": None,
        "model_card": {
            "model_name_en": "Test Model",
            "model_name_ar": "نموذج اختبار",
            "model_type": "LLM",
            "training_data_description_en": "Synthetic data",
            "training_data_description_ar": "بيانات اصطناعية",
            "processes_personal_data": False,
        },
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        create_resp = await client.post("/api/v1/models", json=payload)
        assert create_resp.status_code == 201

        model_id = create_resp.json()["id"]
        get_resp = await client.get(f"/api/v1/models/{model_id}")

    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == model_id
    assert get_resp.json()["name_en"] == "Test Model"
    assert get_resp.json()["name_ar"] == "نموذج اختبار"
    assert get_resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_evaluation_start_returns_202() -> None:
    """POST /api/v1/evaluations must return HTTP 202 with a pending evaluation."""
    payload = {
        "model_id": "test-model-id",
        "use_case_id": "uc-001",
        "engine_config_overrides": {},
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/evaluations", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"
    assert data["verdict"] is None


@pytest.mark.asyncio
async def test_evidence_not_found_returns_404() -> None:
    """GET /api/v1/evidence/{hash} with an unknown hash must return 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/evidence/deadbeef00000000000000000000000000000000000000000000000000000000")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_certificate_not_found_returns_404() -> None:
    """GET /api/v1/certificates/{id} with an unknown ID must return 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/certificates/nonexistent-cert-id")

    assert response.status_code == 404
