"""Use-case catalogue routes.

GET /api/v1/use-cases        -- list all available government use cases
GET /api/v1/use-cases/{id}   -- retrieve a use case with its controls

Fixture data represents the five government use cases defined in
docs/ARCHITECTURE.md section 3. Wave 1 (GOVERNANCE) replaces this with
database-backed records and the full control set.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from mizan.api.schemas import ControlRow, UseCaseDetail, UseCaseRow

router = APIRouter(prefix="/use-cases", tags=["use-cases"])

# ---------------------------------------------------------------------------
# Wave 0 fixture data. Wave 1 (GOVERNANCE) replaces with real DB calls.
# Five government use cases per the charter.
# ---------------------------------------------------------------------------
_FIXTURE_USE_CASES: dict[str, dict] = {
    "uc-001": {
        "id": "uc-001",
        "name_en": "Citizen-Facing Arabic Chatbot",
        "name_ar": "روبوت المحادثة العربي للمواطنين",
        "description_en": (
            "AI model deployed to interact with UAE citizens in Arabic, "
            "providing information about government services."
        ),
        "description_ar": (
            "نموذج ذكاء اصطناعي يتفاعل مع المواطنين الإماراتيين باللغة العربية "
            "لتقديم معلومات حول الخدمات الحكومية."
        ),
        "use_case_class": "citizen_chatbot",
        "confidence_threshold": 0.97,
        "controls": [
            {
                "id": "ctrl-001-001",
                "name_en": "Arabic Language Safety",
                "name_ar": "سلامة اللغة العربية",
                "framework_clause": "Principle 3 - Safety and Reliability",
                "is_mandatory": True,
                "weight": 1.0,
                "suite_id": "suite-arabic-safety",
            },
            {
                "id": "ctrl-001-002",
                "name_en": "Bias and Fairness",
                "name_ar": "التحيز والعدالة",
                "framework_clause": "Principle 5 - Fairness and Non-discrimination",
                "is_mandatory": True,
                "weight": 0.9,
                "suite_id": "suite-bias",
            },
        ],
    },
    "uc-002": {
        "id": "uc-002",
        "name_en": "Internal Document Summarisation",
        "name_ar": "تلخيص الوثائق الداخلية",
        "description_en": (
            "AI model that summarises internal government documents "
            "for use by ministry staff."
        ),
        "description_ar": (
            "نموذج ذكاء اصطناعي يلخص الوثائق الحكومية الداخلية "
            "لاستخدام موظفي الوزارة."
        ),
        "use_case_class": "document_summarisation",
        "confidence_threshold": 0.90,
        "controls": [
            {
                "id": "ctrl-002-001",
                "name_en": "Factual Accuracy",
                "name_ar": "الدقة الواقعية",
                "framework_clause": "Principle 3 - Safety and Reliability",
                "is_mandatory": True,
                "weight": 1.0,
                "suite_id": "suite-capability",
            },
            {
                "id": "ctrl-002-002",
                "name_en": "Information Security",
                "name_ar": "أمن المعلومات",
                "framework_clause": "Principle 6 - Privacy and Security",
                "is_mandatory": True,
                "weight": 0.8,
                "suite_id": "suite-safety",
            },
        ],
    },
    "uc-003": {
        "id": "uc-003",
        "name_en": "Benefits Eligibility Triage",
        "name_ar": "تحديد الأهلية للمزايا الاجتماعية",
        "description_en": (
            "AI model that assists in triaging citizen applications "
            "for government benefits and social support."
        ),
        "description_ar": (
            "نموذج ذكاء اصطناعي يساعد في فرز طلبات المواطنين "
            "للحصول على المزايا الحكومية والدعم الاجتماعي."
        ),
        "use_case_class": "benefits_triage",
        "confidence_threshold": 0.98,
        "controls": [
            {
                "id": "ctrl-003-001",
                "name_en": "Demographic Fairness",
                "name_ar": "العدالة الديموغرافية",
                "framework_clause": "Principle 5 - Fairness and Non-discrimination",
                "is_mandatory": True,
                "weight": 1.0,
                "suite_id": "suite-bias",
            },
            {
                "id": "ctrl-003-002",
                "name_en": "PDPL Compliance",
                "name_ar": "الامتثال لقانون حماية البيانات",
                "framework_clause": "Principle 6 - Privacy and Security",
                "is_mandatory": True,
                "weight": 1.0,
                "suite_id": "suite-safety",
            },
        ],
    },
    "uc-004": {
        "id": "uc-004",
        "name_en": "Traffic Incident Classification",
        "name_ar": "تصنيف حوادث المرور",
        "description_en": (
            "AI model that classifies traffic incidents from sensor "
            "data and operator reports to prioritise response."
        ),
        "description_ar": (
            "نموذج ذكاء اصطناعي يصنف حوادث المرور من بيانات أجهزة الاستشعار "
            "وتقارير المشغلين لترتيب أولويات الاستجابة."
        ),
        "use_case_class": "incident_classification",
        "confidence_threshold": 0.95,
        "controls": [
            {
                "id": "ctrl-004-001",
                "name_en": "Reliability Under Distribution Shift",
                "name_ar": "الموثوقية في ظل تحول التوزيع",
                "framework_clause": "Principle 3 - Safety and Reliability",
                "is_mandatory": True,
                "weight": 1.0,
                "suite_id": "suite-capability",
            },
        ],
    },
    "uc-005": {
        "id": "uc-005",
        "name_en": "Procurement Document Analysis",
        "name_ar": "تحليل وثائق المشتريات",
        "description_en": (
            "AI model that analyses procurement documents to extract "
            "key terms and flag compliance issues."
        ),
        "description_ar": (
            "نموذج ذكاء اصطناعي يحلل وثائق المشتريات لاستخراج "
            "الشروط الرئيسية وتحديد مشكلات الامتثال."
        ),
        "use_case_class": "procurement_analysis",
        "confidence_threshold": 0.92,
        "controls": [
            {
                "id": "ctrl-005-001",
                "name_en": "Bilingual Document Understanding",
                "name_ar": "فهم الوثائق ثنائية اللغة",
                "framework_clause": "MIZAN-CTL-001 (MIZAN-defined control)",
                "is_mandatory": True,
                "weight": 0.9,
                "suite_id": "suite-capability",
            },
        ],
    },
}


@router.get("", response_model=list[UseCaseRow], summary="List government use cases")
async def list_use_cases() -> list[UseCaseRow]:
    """Return all available government use cases."""
    return [
        UseCaseRow(
            id=uc["id"],
            name_en=uc["name_en"],
            name_ar=uc["name_ar"],
            description_en=uc["description_en"],
            description_ar=uc["description_ar"],
            use_case_class=uc["use_case_class"],
            confidence_threshold=uc["confidence_threshold"],
        )
        for uc in _FIXTURE_USE_CASES.values()
    ]


@router.get(
    "/{use_case_id}",
    response_model=UseCaseDetail,
    summary="Retrieve a use case with its controls",
)
async def get_use_case(use_case_id: str) -> UseCaseDetail:
    """Return the full use-case record including all associated controls."""
    uc = _FIXTURE_USE_CASES.get(use_case_id)
    if uc is None:
        raise HTTPException(status_code=404, detail=f"Use case '{use_case_id}' not found.")

    controls = [
        ControlRow(
            id=c["id"],
            name_en=c["name_en"],
            name_ar=c["name_ar"],
            framework_clause=c["framework_clause"],
            is_mandatory=c["is_mandatory"],
            weight=c["weight"],
            suite_id=c["suite_id"],
        )
        for c in uc.get("controls", [])
    ]
    return UseCaseDetail(
        id=uc["id"],
        name_en=uc["name_en"],
        name_ar=uc["name_ar"],
        description_en=uc["description_en"],
        description_ar=uc["description_ar"],
        use_case_class=uc["use_case_class"],
        confidence_threshold=uc["confidence_threshold"],
        controls=controls,
    )
