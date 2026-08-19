#!/usr/bin/env python3
"""MIZAN database seeder.

Populates the registry with a deterministic set of models, use cases,
controls, and engine_memory rows that support the Wave 4 demo.

Usage:
    uv run python scripts/seed.py

The script is idempotent: it uses INSERT OR IGNORE so it is safe to
run on a database that has already been seeded.

Seed data is designed to support the three-minute demo choreography:
  - Eight historical models (six certified, two rejected).
  - Use cases matching the five government categories.
  - engine_memory rows that demonstrate the compounding-registry property
    (faster convergence on second and subsequent evaluations).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add the repo root to sys.path so this script can import mizan.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from mizan.engine.db.database import engine, init_db

# ---------------------------------------------------------------------------
# Deterministic ID generation
# Using fixed UUIDs ensures the demo seed is reproducible and the
# evidence bundle hashes in the Wave 4 seeded certificates are stable.
# ---------------------------------------------------------------------------
def _det_uuid(seed: str) -> str:
    """Generate a deterministic UUID from a seed string via SHA-256."""
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return str(uuid.UUID(digest[:32]))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

USE_CASES = [
    {
        "id": "uc-001",
        "name_en": "Citizen-Facing Arabic Chatbot",
        "name_ar": "روبوت المحادثة العربي للمواطنين",
        "description_en": "AI model deployed to interact with UAE citizens in Arabic, providing information about government services.",
        "description_ar": "نموذج ذكاء اصطناعي يتفاعل مع المواطنين الإماراتيين باللغة العربية لتقديم معلومات حول الخدمات الحكومية.",
        "use_case_class": "citizen_chatbot",
        "confidence_threshold": 0.97,
    },
    {
        "id": "uc-002",
        "name_en": "Internal Document Summarisation",
        "name_ar": "تلخيص الوثائق الداخلية",
        "description_en": "AI model that summarises internal government documents for use by ministry staff.",
        "description_ar": "نموذج ذكاء اصطناعي يلخص الوثائق الحكومية الداخلية لاستخدام موظفي الوزارة.",
        "use_case_class": "document_summarisation",
        "confidence_threshold": 0.90,
    },
    {
        "id": "uc-003",
        "name_en": "Benefits Eligibility Triage",
        "name_ar": "تحديد الأهلية للمزايا الاجتماعية",
        "description_en": "AI model that assists in triaging citizen applications for government benefits and social support.",
        "description_ar": "نموذج ذكاء اصطناعي يساعد في فرز طلبات المواطنين للحصول على المزايا الحكومية والدعم الاجتماعي.",
        "use_case_class": "benefits_triage",
        "confidence_threshold": 0.98,
    },
    {
        "id": "uc-004",
        "name_en": "Traffic Incident Classification",
        "name_ar": "تصنيف حوادث المرور",
        "description_en": "AI model that classifies traffic incidents from sensor data and operator reports to prioritise response.",
        "description_ar": "نموذج ذكاء اصطناعي يصنف حوادث المرور من بيانات أجهزة الاستشعار وتقارير المشغلين لترتيب أولويات الاستجابة.",
        "use_case_class": "incident_classification",
        "confidence_threshold": 0.95,
    },
    {
        "id": "uc-005",
        "name_en": "Procurement Document Analysis",
        "name_ar": "تحليل وثائق المشتريات",
        "description_en": "AI model that analyses procurement documents to extract key terms and flag compliance issues.",
        "description_ar": "نموذج ذكاء اصطناعي يحلل وثائق المشتريات لاستخراج الشروط الرئيسية وتحديد مشكلات الامتثال.",
        "use_case_class": "procurement_analysis",
        "confidence_threshold": 0.92,
    },
]

MODELS = [
    {
        "id": _det_uuid("model-alpha-v1"),
        "name_en": "Alpha LLM v1",
        "name_ar": "نموذج ألفا v1",
        "provider": "Alpha AI",
        "version": "1.0.0",
        "status": "certified",
        "model_card": json.dumps({
            "model_name_en": "Alpha LLM v1",
            "model_name_ar": "نموذج ألفا v1",
            "model_type": "LLM",
            "training_data_description_en": "Multilingual corpus including Arabic government documents.",
            "training_data_description_ar": "مجموعة بيانات متعددة اللغات تشمل وثائق حكومية عربية.",
            "processes_personal_data": False,
        }),
    },
    {
        "id": _det_uuid("model-beta-v2"),
        "name_en": "Beta Classifier v2",
        "name_ar": "نموذج بيتا للتصنيف v2",
        "provider": "Beta Systems",
        "version": "2.0.0",
        "status": "certified",
        "model_card": json.dumps({"model_name_en": "Beta Classifier v2", "model_name_ar": "نموذج بيتا v2", "model_type": "classifier", "training_data_description_en": "Traffic sensor data", "training_data_description_ar": "بيانات أجهزة استشعار المرور", "processes_personal_data": False}),
    },
    {
        "id": _det_uuid("model-gamma-v1"),
        "name_en": "Gamma Chat v1",
        "name_ar": "نموذج غاما للمحادثة v1",
        "provider": "Gamma Corp",
        "version": "1.0.0",
        "status": "rejected",
        "model_card": json.dumps({"model_name_en": "Gamma Chat v1", "model_name_ar": "نموذج غاما v1", "model_type": "LLM", "training_data_description_en": "English-only corpus", "training_data_description_ar": "مجموعة بيانات إنجليزية فقط", "processes_personal_data": False}),
    },
    {
        "id": _det_uuid("model-delta-v3"),
        "name_en": "Delta Summariser v3",
        "name_ar": "نموذج دلتا للتلخيص v3",
        "provider": "Delta AI Research",
        "version": "3.0.0",
        "status": "certified",
        "model_card": json.dumps({"model_name_en": "Delta Summariser v3", "model_name_ar": "نموذج دلتا v3", "model_type": "LLM", "training_data_description_en": "Government document corpus", "training_data_description_ar": "مجموعة وثائق حكومية", "processes_personal_data": True}),
    },
    {
        "id": _det_uuid("model-epsilon-v1"),
        "name_en": "Epsilon Triage v1",
        "name_ar": "نموذج إبسيلون للفرز v1",
        "provider": "Epsilon Labs",
        "version": "1.0.0",
        "status": "certified",
        "model_card": json.dumps({"model_name_en": "Epsilon Triage v1", "model_name_ar": "نموذج إبسيلون v1", "model_type": "classifier", "training_data_description_en": "Social support application data", "training_data_description_ar": "بيانات طلبات الدعم الاجتماعي", "processes_personal_data": True}),
    },
    {
        "id": _det_uuid("model-zeta-v2"),
        "name_en": "Zeta Procurement v2",
        "name_ar": "نموذج زيتا للمشتريات v2",
        "provider": "Zeta Systems",
        "version": "2.0.0",
        "status": "certified",
        "model_card": json.dumps({"model_name_en": "Zeta Procurement v2", "model_name_ar": "نموذج زيتا v2", "model_type": "LLM", "training_data_description_en": "Procurement and legal documents", "training_data_description_ar": "وثائق المشتريات والقانونية", "processes_personal_data": False}),
    },
    {
        "id": _det_uuid("model-eta-v1"),
        "name_en": "Eta Safety v1",
        "name_ar": "نموذج إيتا للسلامة v1",
        "provider": "Eta Research",
        "version": "1.0.0",
        "status": "certified",
        "model_card": json.dumps({"model_name_en": "Eta Safety v1", "model_name_ar": "نموذج إيتا v1", "model_type": "LLM", "training_data_description_en": "Safety-focused Arabic corpus", "training_data_description_ar": "مجموعة بيانات عربية تركز على السلامة", "processes_personal_data": False}),
    },
    {
        "id": _det_uuid("model-theta-v1"),
        "name_en": "Theta Legacy v1",
        "name_ar": "نموذج ثيتا القديم v1",
        "provider": "Theta Inc.",
        "version": "1.0.0",
        "status": "rejected",
        "model_card": json.dumps({"model_name_en": "Theta Legacy v1", "model_name_ar": "نموذج ثيتا v1", "model_type": "LLM", "training_data_description_en": "Deprecated training set", "training_data_description_ar": "مجموعة تدريب قديمة", "processes_personal_data": False}),
    },
]

ENGINE_MEMORY_ROWS = [
    {
        "use_case_class": "citizen_chatbot",
        "suite_ordering": json.dumps(["suite-arabic-safety", "suite-bias", "suite-safety", "suite-capability", "suite-redteam"]),
        "arm_statistics": json.dumps({
            "suite-arabic-safety": {"pulls": 42, "total_reward": 38.1, "mean_reward": 0.907},
            "suite-bias": {"pulls": 28, "total_reward": 24.4, "mean_reward": 0.871},
            "suite-safety": {"pulls": 15, "total_reward": 13.2, "mean_reward": 0.880},
            "suite-capability": {"pulls": 9, "total_reward": 8.0, "mean_reward": 0.889},
            "suite-redteam": {"pulls": 6, "total_reward": 5.4, "mean_reward": 0.900},
        }),
        "total_evaluations": 8,
    },
    {
        "use_case_class": "document_summarisation",
        "suite_ordering": json.dumps(["suite-capability", "suite-safety", "suite-bias"]),
        "arm_statistics": json.dumps({
            "suite-capability": {"pulls": 35, "total_reward": 31.5, "mean_reward": 0.900},
            "suite-safety": {"pulls": 20, "total_reward": 17.0, "mean_reward": 0.850},
            "suite-bias": {"pulls": 10, "total_reward": 8.5, "mean_reward": 0.850},
        }),
        "total_evaluations": 5,
    },
]


async def seed() -> None:
    """Run the seeder against the configured database."""
    await init_db()

    async with engine.begin() as conn:
        await conn.run_sync(_seed_sync)

    print("Seed complete.")


def _seed_sync(connection) -> None:
    cursor = connection.connection.cursor()
    now = _now()

    # Use cases
    for uc in USE_CASES:
        cursor.execute(
            """
            INSERT OR IGNORE INTO use_cases
                (id, name_en, name_ar, description_en, description_ar,
                 use_case_class, confidence_threshold, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uc["id"], uc["name_en"], uc["name_ar"],
                uc["description_en"], uc["description_ar"],
                uc["use_case_class"], uc["confidence_threshold"], now,
            ),
        )

    # Models
    for m in MODELS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO models
                (id, name_en, name_ar, provider, version, status,
                 model_card, submitted_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                m["id"], m["name_en"], m["name_ar"],
                m["provider"], m["version"], m["status"],
                m["model_card"], now, now,
            ),
        )

    # Engine memory
    for row in ENGINE_MEMORY_ROWS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO engine_memory
                (use_case_class, suite_ordering, arm_statistics,
                 total_evaluations, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row["use_case_class"], row["suite_ordering"],
                row["arm_statistics"], row["total_evaluations"], now,
            ),
        )

    connection.connection.commit()
    print(f"  Inserted {len(USE_CASES)} use cases, {len(MODELS)} models, "
          f"{len(ENGINE_MEMORY_ROWS)} engine_memory rows.")


if __name__ == "__main__":
    asyncio.run(seed())
