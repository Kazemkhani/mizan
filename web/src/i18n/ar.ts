/**
 * Arabic (ar-AE) string catalogue for the MIZAN web shell.
 *
 * All strings must be in formal Gulf governmental register.
 * Owned by RASHID (Principal Arabic NLP and Localisation Lead).
 * Wave 0 provides initial translations; RASHID reviews and corrects
 * in Wave 1 to ensure authentic Emirati governmental register.
 *
 * NOTE TO RASHID: strings marked [REVIEW] require particular attention
 * to Gulf governmental register. Do not accept MSA press style.
 */
export const ar: Record<string, string> = {
  // Application identity
  'app.name': 'ميزان',
  'app.tagline': 'سجل نماذج الذكاء الاصطناعي السيادي ومحرك الامتثال التكيفي', // [REVIEW]

  // Navigation
  'nav.registry': 'السجل',
  'nav.evaluate': 'التقييم',
  'nav.certificates': 'الشهادات',
  'nav.about': 'عن النظام',

  // Language toggle
  'lang.toggle.label': 'التبديل إلى الإنجليزية',
  'lang.current': 'العربية',

  // Registry page
  'registry.title': 'سجل النماذج',
  'registry.subtitle': 'جميع نماذج الذكاء الاصطناعي المقدمة لتقييم الامتثال الحكومي.', // [REVIEW]
  'registry.status.pending': 'قيد الانتظار',
  'registry.status.in_evaluation': 'قيد التقييم',
  'registry.status.certified': 'معتمد',
  'registry.status.rejected': 'مرفوض',
  'registry.empty': 'لم يتم تسجيل أي نماذج بعد.',

  // Evaluation page
  'evaluation.title': 'بدء التقييم',
  'evaluation.model.label': 'النموذج',
  'evaluation.use_case.label': 'حالة الاستخدام',
  'evaluation.submit': 'بدء التقييم',
  'evaluation.streaming.title': 'التقييم جارٍ',
  'evaluation.streaming.awaiting': 'في انتظار محرك التقييم...',

  // Certificate page
  'certificate.title': 'شهادة الامتثال',
  'certificate.verdict.certified': 'معتمد',
  'certificate.verdict.rejected': 'مرفوض',
  'certificate.evidence_hash': 'تجزئة حزمة الأدلة',
  'certificate.issued': 'تاريخ الإصدار',
  'certificate.download_pdf': 'تنزيل شهادة PDF',

  // Common
  'common.loading': 'جارٍ التحميل...',
  'common.error': 'حدث خطأ.',
  'common.back': 'رجوع',
  'common.view': 'عرض',
}
