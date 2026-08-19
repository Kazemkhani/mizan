/**
 * Arabic (ar-AE) strings for the landing page, the platform interface and
 * the guided walkthrough.
 *
 * Register standard: formal Gulf governmental register, as recorded in
 * ar.ts. These strings are new in this wave and are written to that
 * standard; they carry a RASHID review flag because they have not yet been
 * through the Arabic register review that ar.ts records.
 *
 * Every key here has a counterpart in en.interface.ts.
 */
export const arInterface: Record<string, string> = {
  // ---------------------------------------------------------------- landing
  'landing.nav.how': 'آلية العمل',
  'landing.nav.data': 'البيانات الحكومية',
  'landing.nav.usecases': 'حالات الاستخدام',
  'landing.nav.limits': 'حدود الأداة',
  'landing.hero.eyebrow': 'بما يتوافق مع استراتيجية الإمارات الوطنية للذكاء الاصطناعي 2031',
  'landing.hero.title': 'اعتماد أنظمة الذكاء الاصطناعي قبل دخولها الخدمة الحكومية',
  'landing.hero.lede':
    'تعتمد الدول الطائرات قبل إقلاعها والأدوية قبل توزيعها. وميزان هو الأداة المكافئة لنموذج ذكاء اصطناعي يدخل الخدمة الحكومية: سجل، ومحرك تقييم يتوقف عن اختبار الضابط فور استقرار الأدلة عليه، وشهادة موقَّعة ثنائية اللغة تُظهر أساس كل حكم.',
  'landing.hero.enter': 'الدخول إلى ميزان',
  'landing.hero.tour': 'كيف تعمل',
  'landing.hero.caption': 'لا يلزم إنشاء حساب. ولا يغادر ما تُدخله هذا الجهاز.',
  'landing.stat.controls': 'ضابطاً في السجل',
  'landing.stat.usecases': 'حالات استخدام حكومية',
  'landing.stat.entities': 'جهات ناشرة للبيانات',
  'landing.stat.languages': 'لغتان أصليتان',
  'landing.stat.languages.value': 'العربية والإنجليزية',

  'landing.what.title': 'ما الذي يمكنك القيام به هنا',
  'landing.what.lede': 'أربع خطوات في جلسة واحدة. ويرافقك الدليل الإرشادي في الداخل عبرها بمثال عملي.',
  'landing.step.one.title': 'تسجيل النموذج',
  'landing.step.one.body':
    'ارفع ملف الطلب أو املأ النموذج المختصر. ويتضمَّن الطلب بطاقة النموذج: ماهيته، وبيانات تدريبه، وما إذا كان يعالج بيانات شخصية، والحدود التي يُقرّ بها مالكه.',
  'landing.step.two.title': 'اختيار حالة الاستخدام',
  'landing.step.two.body':
    'يخضع روبوت المحادثة العربي الموجَّه للمواطنين لمعيار يختلف عن أداة التلخيص الداخلية. واختيار حالة الاستخدام يحدِّد الضوابط وأوزانها ومستوى الثقة الواجب بلوغه.',
  'landing.step.three.title': 'متابعة تجمُّع الأدلة',
  'landing.step.three.body':
    'يختار المحرك الاختبار التالي وفق أسرعها حسماً للقرار، ويتوقف عن اختبار الضابط فور استقرار أدلته. وترى كل اختبار والإجابة التي استدعاها والدرجة التي نالها لحظة حدوثه.',
  'landing.step.four.title': 'قراءة الشهادة',
  'landing.step.four.body':
    'يرتبط كل حكم بالاختبار الذي أنتجه، ويحمل كل اختبار بصمة SHA-256. والضابط الذي نجح دون إثبات إحصائي يُصرَّح بذلك على وجه الشهادة.',

  'landing.principles.title': 'ثلاثة التزامات',
  'landing.principle.arabic.title': 'العربية لغة أصلية لا مترجَمة',
  'landing.principle.arabic.body':
    'ليست طبقة ترجمة. فالمجموعات الاختبارية والهجمات والشهادات وهذه الواجهة موجودة أصلاً بالعربية باتجاه صحيح من اليمين إلى اليسار. والنموذج الآمن بالإنجليزية وغير الآمن بالعربية راسب.',
  'landing.principle.evidence.title': 'الدليل مقدَّم على الادعاء',
  'landing.principle.evidence.body':
    'الأدلة قابلة للإضافة فقط، بفرض من مشغلات قاعدة البيانات وسلسلة بصمات لكل تقييم لا بالعُرف، بحيث يمكن كشف أي تعديل أو حذف بالتتبُّع.',
  'landing.principle.limits.title': 'الأداة تُصرِّح بحدودها',
  'landing.principle.limits.body':
    'تميِّز الشهادة بين ضابط حُسم بحدٍّ ثقةٍ إحصائي وضابط حُسم عند نفاد مجموعة الاختبارات، وتطبع الحد الذي ناله كل ضابط فعلياً.',

  'landing.data.title': 'البيانات الحكومية التي يستند إليها التقييم',
  'landing.data.lede':
    'ترتبط حالات الاستخدام ببيانات منشورة فعلياً لا بسياق متخيَّل. وقد جرى جلب كل ارتباط والتحقق من بصمته، وقُرئ كل حقل في هذه البطاقات من بيان الجلب نفسه.',
  'landing.data.note':
    'العلامات الظاهرة أدناه رموز طباعية من إعداد ميزان وليست شعارات رسمية. وتذكر كل بطاقة الجهة الناشرة وتُحيل إلى البوابة التي تنشر عبرها.',
  'landing.data.field.dataset': 'مجموعة البيانات كما نُشرت',
  'landing.data.field.portal': 'البوابة',
  'landing.data.field.resource': 'مُعرِّف المورد',
  'landing.data.field.read': 'تاريخ القراءة',
  'landing.data.field.usecase': 'تدعم',
  'landing.data.open': 'فتح البوابة',

  'landing.usecases.title': 'خمس حالات استخدام حكومية',
  'landing.usecases.lede':
    'لكل حالة مجموعة ضوابطها وأوزانها ومستوى الثقة الخاص بها، وفق ما هو مسجَّل في السجل المنشور.',
  'landing.usecases.controls': 'ضابطاً',
  'landing.usecases.mandatory': 'إلزامي',
  'landing.usecases.threshold': 'مستوى الثقة المطلوب',

  'landing.limits.title': 'ما ليست عليه هذه الأداة',
  'landing.limits.body':
    'هذا عمل بحجم تجريبي. ومجموعة الاختبارات أصغر مما يتطلبه الإسناد الإحصائي الكامل، ولذلك يُحسم كثير من الضوابط الناجحة عند نفاد المجموعة لا بحدِّ ثقة، وتُصرِّح الشهادة بذلك لكل ضابط. وتُسجِّل شهادة ميزان المطابقة لمجموعة ضوابط ميزان، وهي ليست رأياً قانونياً ولا اعتماداً من أي جهة حكومية.',
  'landing.footer.note': 'سجل سيادي لتقييم الذكاء الاصطناعي. جميع الحقوق محفوظة.',

  // --------------------------------------------------------------- platform
  'console.back': 'العودة إلى صفحة التعريف',
  'console.guide': 'الدليل',
  'console.guide.restart': 'إعادة تشغيل الدليل الإرشادي',
  'console.mode.live': 'متصل بمحرك التقييم',
  'console.mode.recorded': 'إعادة عرض لتقييم مُسجَّل',
  'console.mode.recorded.detail':
    'لا يمكن الوصول إلى محرك من هذه الصفحة، ولذلك يعيد ميزان عرض تقييمات سجَّلها المحرك الفعلي على مجموعة الاختبارات الفعلية. وكل خطوة وحكم وبصمة تظهر هنا من إنتاج المحرك.',
  'console.mode.live.detail':
    'هذه الصفحة متصلة بواجهة برمجة ميزان. والتقييمات التي تبدؤها تُنفَّذ فعلياً وتكتب أدلتها في السجل.',

  'console.step.submit': 'التقديم',
  'console.step.usecase': 'حالة الاستخدام',
  'console.step.evaluate': 'التقييم',
  'console.step.certificate': 'الشهادة',
  'console.step.of': 'الخطوة {n} من 4',

  'submit.title': 'تقديم نموذج للتقييم',
  'submit.lede':
    'أفلِت ملف الطلب في الأسفل. والطلب ملف JSON صغير يبيّن الجهة المطوِّرة وماهية النموذج وبطاقة النموذج التي يلتزم بها مالكه.',
  'submit.drop': 'أفلِت ملف الطلب هنا',
  'submit.browse': 'أو اختر ملفاً',
  'submit.samples.title': 'لا يتوفر لديك ملف؟ اختر أحد هذه الملفات.',
  'submit.samples.lede':
    'ثلاثة طلبات مُعدَّة مسبقاً يسلك كلٌّ منها مساراً مختلفاً في التقييم. نزِّل أحدها ثم أفلِته في الأعلى.',
  'submit.sample.compliant.name': 'مساعد عربي ممتثل',
  'submit.sample.compliant.detail': 'بطاقة نموذج مكتملة ونموذج يجيب بأمان باللغتين. والنتيجة المتوقعة شهادة اعتماد.',
  'submit.sample.non_compliant.name': 'نموذج متعدد اللغات غير آمن',
  'submit.sample.non_compliant.detail': 'يرفض الأسئلة المشروعة ويستجيب للطلبات الضارة بالعربية. والنتيجة المتوقعة رفض مبكر.',
  'submit.sample.incomplete.name': 'نموذج غير موثَّق',
  'submit.sample.incomplete.detail': 'نموذج قادر ببطاقة نموذج ناقصة. والنتيجة المتوقعة رسوب الضوابط المستندية.',
  'submit.sample.download': 'تنزيل',
  'submit.file.accepted': 'تمت قراءة الطلب',
  'submit.file.rejected': 'تعذَّرت قراءة هذا الملف بوصفه طلباً في ميزان.',
  'submit.field.provider': 'الجهة المطوِّرة',
  'submit.field.version': 'الإصدار',
  'submit.field.served': 'يُقدَّم عبر',
  'submit.served.mock': 'محوِّل محاكاة حتمي، النمط {profile}',
  'submit.served.endpoint': 'نقطة اتصال مباشرة',
  'submit.register': 'تسجيل هذا النموذج',
  'submit.registered': 'مُسجَّل',
  'submit.registry.title': 'السجل',
  'submit.registry.lede': 'النماذج المُودَعة في هذا السجل.',

  'usecase.title': 'اختر حالة الاستخدام المقصودة',
  'usecase.lede':
    'هذا هو الاختيار الحاسم، إذ يحدِّد الضوابط المنطبقة ووزن كل منها ومستوى الثقة الواجب بلوغه قبل إصدار الشهادة.',
  'usecase.selected': 'مختارة',
  'usecase.select': 'اختيار',
  'usecase.datasets': 'مستندة إلى بيانات تنشرها',

  'evaluate.title': 'المفاضلة والحسم',
  'evaluate.lede':
    'يختار المحرك الاختبار التالي وفق أسرعها حسماً للقرار، ويُنهي الضابط فور استقرار أدلته.',
  'evaluate.start': 'بدء التقييم',
  'evaluate.restart': 'إعادة التشغيل',
  'evaluate.running': 'التقييم قيد التنفيذ',
  'evaluate.complete': 'اكتمل التقييم',
  'evaluate.speed': 'السرعة',
  'evaluate.speed.steady': 'متأنية',
  'evaluate.speed.fast': 'سريعة',
  'evaluate.probes': 'الاختبارات المُجراة',
  'evaluate.controls.settled': 'الضوابط ذات الأدلة',
  'evaluate.stream.title': 'تدفُّق الاختبارات',
  'evaluate.stream.empty': 'يمتلئ التدفُّق كلما سحب المحرك اختباراً.',
  'evaluate.controls.title': 'لوحة الضوابط',
  'evaluate.controls.hint': 'اختر أي ضابط لقراءة التبادل الذي يقف خلفه.',
  'evaluate.passed': 'ناجح',
  'evaluate.failed': 'راسب',
  'evaluate.awaiting': 'بانتظار الأدلة',
  'evaluate.stopped.corpus_exhausted': 'توقَّف: نفدت مجموعة الاختبارات',
  'evaluate.stopped.mandatory_control_failed': 'توقَّف: رسب ضابط إلزامي',
  'evaluate.stopped.hoeffding_bound_met': 'توقَّف: حُسمت جميع الضوابط الإلزامية',
  'evaluate.stopped.budget_exhausted': 'توقَّف: استُنفدت ميزانية الاختبارات',
  'evaluate.verdict.certified': 'معتمد',
  'evaluate.verdict.rejected': 'غير معتمد',
  'evaluate.view.certificate': 'فتح الشهادة',

  'evidence.title': 'التبادل الذي أنتج هذه الدرجة',
  'evidence.prompt': 'الاختبار',
  'evidence.response': 'استجابة النموذج',
  'evidence.response.attestation': 'حُسم استناداً إلى بطاقة النموذج لا إلى اختبار.',
  'evidence.scorer': 'أداة التقييم',
  'evidence.score': 'الدرجة',
  'evidence.hash': 'بصمة الدليل SHA-256',
  'evidence.control': 'الضابط',
  'evidence.close': 'إغلاق',
  'evidence.empty': 'اختر اختباراً من التدفُّق لعرضه هنا.',

  'cert.title': 'الشهادة',
  'cert.none': 'تظهر الشهادة هنا فور بلوغ التقييم حكماً نهائياً.',
  'cert.tier.statistical': 'المستوى الإحصائي: نال كل ضابط إلزامي حدَّ ثقة.',
  'cert.tier.budget': 'مستوى الميزانية: حُسم ضابط إلزامي واحد أو أكثر دون حدِّ ثقة، وكلٌّ منها مؤشَّر أدناه.',
  'cert.model': 'النموذج',
  'cert.usecase': 'حالة الاستخدام',
  'cert.issued': 'تاريخ الإصدار',
  'cert.bundle': 'بصمة حزمة الأدلة',
  'cert.signature': 'التوقيع',
  'cert.controls': 'نتائج الضوابط',
  'cert.control.basis': 'أساس القرار',
  'cert.control.probes': 'الاختبارات',
  'cert.control.bound': 'الحد الأدنى المُحقَّق',
  'cert.control.required': 'المطلوب',
  'cert.datasets': 'مجموعات البيانات المُعتمَدة',
  'cert.asserts': 'ما تُثبته هذه الشهادة',
  'cert.does_not': 'ما لا تُثبته',
  'cert.validity': 'السريان',
  'cert.download': 'تنزيل الشهادة بصيغة JSON',
  'cert.print': 'طباعة',
  'cert.served': 'جهة تقديم التقييم',

  // ------------------------------------------------------------ walkthrough
  'tour.next': 'التالي',
  'tour.back': 'السابق',
  'tour.skip': 'تخطي الدليل',
  'tour.done': 'ابدأ الاستخدام',
  'tour.progress': '{n} من {total}',
  'tour.welcome.title': 'مرحباً بك في ميزان',
  'tour.welcome.body':
    'يستغرق هذا الدليل نحو دقيقة، ويبيّن كيف ينتقل النموذج من ملف طلب إلى شهادة موقَّعة. ويمكنك الخروج منه في أي لحظة والعودة إليه من زر الدليل.',
  'tour.submit.title': 'ابدأ بالطلب',
  'tour.submit.body':
    'نزِّل أحد الطلبات المُعدَّة وأفلِته في اللوحة. وإن أردت المسار الناجح فاختر المساعد العربي الممتثل.',
  'tour.registry.title': 'السجل',
  'tour.registry.body':
    'يظهر كل ما يُودَع هنا في السجل مع حالته: قيد الانتظار، أو قيد التقييم، أو معتمد، أو غير معتمد.',
  'tour.usecase.title': 'حالة الاستخدام تحدِّد المعيار',
  'tour.usecase.body':
    'اختر حالة الاستخدام المقصودة. ويستوجب روبوت المحادثة العربي الموجَّه للمواطنين أوسع مجموعة ضوابط وأعلى مستوى ثقة بين الحالات الخمس.',
  'tour.evaluate.title': 'تابع الحسم',
  'tour.evaluate.body':
    'ابدأ التقييم. تصل الاختبارات على جانب وتُحسم الضوابط على الجانب الآخر. ولا شيء محسوب مسبقاً: يُنهى كل ضابط فور استقرار أدلته.',
  'tour.evidence.title': 'افتح أي اختبار',
  'tour.evidence.body':
    'اختر اختباراً من التدفُّق أو ضابطاً من اللوحة لقراءة نص الاختبار وإجابة النموذج وبصمة السجل.',
  'tour.certificate.title': 'الشهادة',
  'tour.certificate.body':
    'عند صدور الحكم تُصدَر الشهادة باللغتين، ضابطاً ضابطاً، مع القوة الإحصائية التي ناله كل ضابط فعلياً.',

  // ------------------------------------------------------------------ misc
  'common.close': 'إغلاق',
  'common.optional': 'اختياري',
  'common.mandatory': 'إلزامي',
  'common.advisory': 'استرشادي',
  'common.probes': 'اختباراً',
  'common.step': 'الخطوة',
  'common.continue': 'متابعة',
}
