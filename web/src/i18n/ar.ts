/**
 * Arabic (ar-AE) string catalogue for the MIZAN web shell.
 *
 * Register standard: formal Gulf governmental register.
 * The reference register is that of TDRA circulars and Cabinet resolutions,
 * not Egyptian or Levantine press style, and not customer-service chatbot style.
 *
 * Owned by RASHID (Principal Arabic NLP and Localisation Lead).
 * Wave 0: initial scaffold strings.
 * Wave 1: corrected and extended by RASHID to authentic Emirati governmental register.
 *
 * Key register decisions applied in Wave 1:
 *
 *   app.tagline  [REVIEW resolved]:
 *     "السِجَل السيادي" follows the Emirati federal model: the definite noun
 *     precedes its qualifying adjective. "منظومة" (system/framework) is the
 *     standard term UAE federal entities use for integrated digital platforms.
 *
 *   registry.subtitle  [REVIEW resolved]:
 *     "يتضمَّن ... كافة ... المُودَعة" is declarative, passive-participial
 *     government register. "المُودَعة" (deposited/filed) is the correct
 *     administrative verb for formal submissions; "المُقدَّمة" reads as press style.
 *
 *   evaluation.streaming.title:
 *     "قيد التنفيذ" is the standard Gulf federal phrase for processes in progress.
 *     Compare: "المشروع قيد التنفيذ". It replaces the newspaper-style "جارٍ".
 *
 *   certificate.download_pdf:
 *     "بصيغة PDF" (in PDF format) is grammatically complete formal Arabic.
 *     The bare juxtaposition "شهادة PDF" in the Wave 0 string is press-register.
 *
 * RTL and bidirectional text:
 *   I18nProvider sets dir="rtl" on the document root; no per-string override is needed.
 *   Mixed Arabic/Latin strings are handled by the Unicode Bidirectional Algorithm (UBA).
 *   Do not add unicode-bidi or direction overrides to individual strings.
 *   See docs/DESIGN_SYSTEM.md section 4 for the full policy.
 *
 * BiDi hazard: 'certificate.download_pdf' contains a terminal LTR sequence ("PDF").
 *   UBA resolves this correctly in an RTL paragraph: visual order is
 *   [PDF] [بصيغة] [الشهادة] [تنزيل], which reads naturally in Arabic.
 *   No override is applied. Flagged here for Wave 3 visual verification.
 */
export const ar: Record<string, string> = {
  // Application identity
  'app.name': 'ميزان',
  'app.tagline': 'السِجَل السيادي لنماذج الذكاء الاصطناعي ومنظومة الامتثال التكيُّفية',

  // Navigation
  'nav.registry': 'السجل',
  'nav.evaluate': 'التقييم',
  'nav.certificates': 'الشهادات',
  'nav.about': 'نبذة عن المنظومة',

  // Language toggle
  'lang.toggle.label': 'التحويل إلى اللغة الإنجليزية',
  'lang.current': 'العربية',

  // Registry page
  'registry.title': 'سجل النماذج',
  'registry.subtitle': 'يتضمَّن هذا السجل كافة نماذج الذكاء الاصطناعي المُودَعة للتقييم وفق معايير الامتثال الحكومي.',
  'registry.status.pending': 'قيد الانتظار',
  'registry.status.in_evaluation': 'قيد التقييم',
  'registry.status.certified': 'معتمد',
  'registry.status.rejected': 'مرفوض',
  'registry.empty': 'لم تُودَع أي نماذج في السجل بعد.',
  'registry.model_id.label': 'معرِّف النموذج',
  'registry.submitted_at.label': 'تاريخ الإيداع',

  // Model registration
  'model.name.label': 'اسم النموذج',
  'model.endpoint.label': 'عنوان نقطة الاتصال',
  'model.provider.label': 'الجهة المُشغِّلة',
  'model.submit': 'تسجيل النموذج في السجل',

  // Evaluation page
  'evaluation.title': 'بدء التقييم',
  'evaluation.model.label': 'النموذج',
  'evaluation.use_case.label': 'حالة الاستخدام',
  'evaluation.submit': 'تقديم طلب التقييم',
  'evaluation.streaming.title': 'التقييم قيد التنفيذ',
  'evaluation.streaming.awaiting': 'في انتظار استجابة منظومة التقييم...',
  'evaluation.verdict.certified': 'معتمد',
  'evaluation.verdict.rejected': 'مرفوض',
  'evaluation.stopping_reason.hoeffding_bound_met': 'بلوغ عتبة الثقة المطلوبة',
  'evaluation.stopping_reason.mandatory_control_failed': 'فشل ضابط إلزامي',
  'evaluation.stopping_reason.budget_exhausted': 'استنفاد ميزانية التقييم',
  'evaluation.arm_pull.label': 'خطوة المحرك',
  'evaluation.confidence.label': 'مستوى الثقة',

  // Evidence
  'evidence.probe_id.label': 'معرِّف المسبار',
  'evidence.score.label': 'النتيجة',
  'evidence.passed.yes': 'ناجح',
  'evidence.passed.no': 'راسب',

  // Certificate page
  'certificate.title': 'شهادة الامتثال',
  'certificate.verdict.certified': 'معتمد',
  'certificate.verdict.rejected': 'مرفوض',
  'certificate.evidence_hash': 'بصمة حزمة الأدلة',
  'certificate.issued': 'تاريخ الإصدار',
  // BiDi note: terminal LTR sequence "PDF" is handled by UBA; no override applied.
  'certificate.download_pdf': 'تنزيل الشهادة بصيغة PDF',
  'certificate.controls.heading': 'تقييمات الضوابط',
  'certificate.model.heading': 'تفاصيل النموذج',
  'certificate.use_case.heading': 'حالة الاستخدام',
  'certificate.signature.label': 'التوقيع الرقمي',
  'certificate.evaluator.label': 'المُقيِّم',

  // Common
  'common.loading': 'جارٍ التحميل...',
  'common.error': 'حدث خطأ في النظام.',
  'common.back': 'العودة',
  'common.view': 'عرض',
  'common.not_found': 'غير موجود.',
  'common.retry': 'إعادة المحاولة',
  'common.download': 'تنزيل',
  'common.id.label': 'المُعرِّف',
}
