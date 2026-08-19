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
  'console.step.remediate': 'المعالجة',
  'console.step.of': 'الخطوة {n} من 5',

  'submit.title': 'تقديم نموذج للتقييم',
  'submit.lede':
    'أفلِت ملف الطلب في الأسفل. والطلب ملف JSON صغير يبيّن الجهة المطوِّرة وماهية النموذج وبطاقة النموذج التي يلتزم بها مالكه.',
  'submit.drop': 'أفلِت ملف الطلب هنا',
  'submit.browse': 'أو اختر ملفاً',
  'submit.samples.title': 'لا يتوفر لديك ملف؟ اختر أحد هذه الملفات.',
  'submit.samples.lede':
    'ثلاثة طلبات مُعدَّة مسبقاً يسلك كلٌّ منها مساراً مختلفاً في التقييم. حمِّل أحدها مباشرةً في اللوحة، أو نزِّل الملف وأفلِته من جديد.',
  'submit.sample.compliant.name': 'مساعد عربي ممتثل',
  'submit.sample.compliant.detail': 'بطاقة نموذج مكتملة ونموذج يجيب بأمان باللغتين. والنتيجة المتوقعة شهادة اعتماد.',
  'submit.sample.non_compliant.name': 'نموذج متعدد اللغات غير آمن',
  'submit.sample.non_compliant.detail': 'يرفض الأسئلة المشروعة ويستجيب للطلبات الضارة بالعربية. والنتيجة المتوقعة رفض مبكر.',
  'submit.sample.incomplete.name': 'نموذج غير موثَّق',
  'submit.sample.incomplete.detail': 'نموذج قادر ببطاقة نموذج ناقصة. والنتيجة المتوقعة رسوب الضوابط المستندية.',
  'submit.sample.use': 'تحميل هذا الطلب',
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
  'evaluate.view.remediation': 'معالجة الفجوات',

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

  // -------------------------------------------------------- remediation
  'remediate.eyebrow': 'ما بعد الحكم',
  'remediate.title': 'معالجة الفجوات ثم العودة',
  'remediate.lede':
    'يصل كل نموذج ولديه فجوات، حتى النموذج الذي ينال الاعتماد: فعند الحجم الحالي لمجموعة الاختبارات تُحسم معظم الضوابط عند نفاد الاختبارات لا بحدِّ ثقة. تقرأ هذه المرحلة تلك الفجوات من نتيجة التقييم، وتحدِّد العمل اللازم لسدِّها، وتعرض محاكاةً لذلك العمل، ثم تعيد النسخة المُعاد تدريبها إلى المحرك.',
  'remediate.none': 'نفِّذ تقييماً أولاً، فالفجوات تُقرأ من نتيجته.',
  'remediate.phase.gaps': 'الفجوات المرصودة',
  'remediate.phase.plan': 'العمل المطلوب',
  'remediate.phase.training': 'إعادة التدريب',
  'remediate.phase.ready': 'العودة إلى المحرك',
  'remediate.projection': 'إسقاط تقديري. لا شيء في هذه اللوحة دليلٌ، ولا يصلح أيٌّ منه لإصدار شهادة.',
  'remediate.simulated': 'تشغيل محاكى. لا يدرِّب ميزان النماذج ولا يراقب تدريبها، وإنما تُحاكى هنا سلسلة الخطوات التي تتبعها دورة المعالجة.',
  'remediate.gaps.measured': 'قياس فعلي. كل رقم أدناه مقروء من حالات الضوابط التي أنتجها المحرك ومن الاختبارات التي سحبها.',
  'remediate.gaps.total': 'الفجوات المرصودة',
  'remediate.gaps.failing': 'سلوك راسب',
  'remediate.gaps.unproven': 'ضوابط غير مُثبَتة',
  'remediate.gaps.mandatory': 'الإلزامي منها',
  'remediate.gaps.next': 'عرض العمل المطلوب',
  'remediate.gap.needs': 'الاختبارات اللازمة',
  'remediate.gap.open': 'فتح التبادل',
  'remediate.kind.failing': 'راسب',
  'remediate.kind.intermittent': 'متقطِّع',
  'remediate.kind.unproven': 'غير مُثبَت',
  'remediate.kind.untested': 'لم يُختبَر',
  'remediate.reading.failing':
    'صدر القرار ضد النموذج في هذا الضابط، ويلزم تغيير السلوك قبل أن تصبح الشهادة ممكنة.',
  'remediate.reading.intermittent':
    'نجح النموذج في معظم الاختبارات ورسب في بعضها. والرسوب المتقطِّع في ضابط إلزامي رسوبٌ.',
  'remediate.reading.unproven':
    'لم تُرصد أي مخالفة، غير أن مجموعة الاختبارات نفدت قبل إثبات المعدل المطلوب عند مستوى الثقة المُعلَن. وقد يكون السلوك سليماً، لكن الدليل لم يكتمل بعد.',
  'remediate.reading.untested':
    'لم يسحب هذا الضابط أي اختبار في هذا التقييم، فلا يُعرف عنه شيء في أي اتجاه.',
  'remediate.severity.critical': 'حرج',
  'remediate.severity.high': 'مرتفع',
  'remediate.severity.moderate': 'متوسط',
  'remediate.plan.lede':
    'بند عمل واحد لكل مجال ضوابط، لأن هذه هي الوحدة التي يُشترى بها الإصلاح: فالنموذج لا يكتسب سلوك الرفض بالعربية ضابطاً ضابطاً. وأحجام المجموعات تقديرات تخطيطية بواقع {ratio} عنصراً لكل اختبار يستوجبه السجل، أي {items} عنصراً إجمالاً.',
  'remediate.plan.next': 'تشغيل إعادة التدريب',
  'remediate.fix.controls': 'الضوابط التي يحسمها',
  'remediate.fix.probes': 'الاختبارات المطلوبة',
  'remediate.fix.corpus': 'المجموعة المقترحة',
  'remediate.fix.target': 'المعدل الواجب بلوغه',
  'remediate.fix.source':
    'مستمدة من البيانات الحكومية المرتبطة بـ {useCase}، بحيث تطابق المفردات والسجل اللغوي ما سيواجهه النموذج في الخدمة.',
  'remediate.uplift.title': 'أين يصل هذا العمل',
  'remediate.uplift.lede':
    'المعدل المرصود مقابل المعدل الذي يستوجبه السجل. والرقم الثاني هو الاشتراط لا النتيجة: وحده تقييم جديد يبيّن ما تحققه النسخة المُعاد تدريبها.',
  'remediate.handback.title': 'العودة إلى المحرك',
  'remediate.handback.body':
    'لا يصلح الإسقاط التقديري لاعتماد شيء. قدِّم النسخة المُعاد تدريبها بوصفها إصداراً جديداً ودع المحرك يحكم عليها: فالشهادة سارية للإصدار المُقيَّم تحديداً، ومن ثمَّ فالنموذج المُعاد تدريبه طلبٌ جديد لا تعديلٌ على القديم.',
  'remediate.handback.action': 'تقديم النسخة المُعاد تدريبها',
  'remediate.rerun.note':
    'إعادة تقييم النسخة المُعاد تدريبها، وهي تحمل الإصلاحات الواردة في خطة المعالجة.',

  'retrain.progress': 'المرحلة {n} من {total}، اكتمل {percent}%',
  'retrain.stage.corpus.title': 'تجهيز المجموعة',
  'retrain.stage.corpus.body':
    'تأليف {items} عنصراً في المجالات الراسبة، بالعربية أصالةً حيثما كان الضابط عربياً، مع حجز خُمسها جانباً كي لا يُقيَّم التشغيل الارتدادي على ما دُرِّب عليه.',
  'retrain.stage.corpus.done': 'اكتمل تجهيز المجموعة وحُجزت العينة المُستبقاة',
  'retrain.stage.alignment.title': 'مسارات المواءمة',
  'retrain.stage.alignment.body':
    'ضبط {model} على المجموعة المُجهَّزة، مع التحقق بعد كل مسار من أن السلوك خارج المجالات المستهدفة لم يتغير.',
  'retrain.stage.alignment.done': 'اكتملت مسارات المواءمة دون تراجع خارج الأهداف',
  'retrain.stage.guardrails.title': 'الضوابط الوقائية وموجِّه النظام',
  'retrain.stage.guardrails.body':
    'ربط التغييرات التي لا محل لها في الأوزان: توجيه الرفض، ومسار التصعيد إلى موظف بشري، وحجب البيانات الشخصية، والإفصاح عن الهوية عند بدء الجلسة.',
  'retrain.stage.guardrails.done': 'رُبطت الضوابط الوقائية واختُبر مسار التصعيد',
  'retrain.stage.documentation.title': 'بطاقة النموذج',
  'retrain.stage.documentation.body':
    'استكمال الحقول التي تقرؤها الضوابط المستندية. فالضابط المحسوم على بطاقة النموذج يرسب على حقل فارغ مهما كان سلوك النموذج.',
  'retrain.stage.documentation.done': 'اكتملت بطاقة النموذج وفق الضوابط المستندية',
  'retrain.stage.regression.title': 'التشغيل الارتدادي لدى المالك',
  'retrain.stage.regression.body':
    'تشغيل بنود العمل البالغة {fixes} على العينة المُستبقاة قبل أي تقديم، حتى لا يكون ميزان أول من يرى رسوباً.',
  'retrain.stage.regression.done': 'التشغيل الارتدادي نظيف على العينة المُستبقاة، جاهز للتقديم',

  'fix.safety.action': 'رفض الطلبات الضارة باللغتين',
  'fix.safety.method':
    'تدريب على الرفض بمجموعة خصومية مؤلَّفة أصالةً بالعربية والإنجليزية، مع اشتراط ثبات الرفض عند إعادة الصياغة وتقمُّص الأدوار.',
  'fix.arabic_linguistic.action': 'الإجابة عن العربية بالعربية وبالسجل الحكومي',
  'fix.arabic_linguistic.method':
    'بيانات تعليمات مكتوبة أصالةً بالعربية الفصحى بمفردات حكومية منشورة، مع استبعاد العناصر المترجمة: فمجموعة الرفض المترجمة هي التي أنتجت هذه الفجوة.',
  'fix.privacy.action': 'عدم إعادة إظهار البيانات الشخصية أو الاحتفاظ بها',
  'fix.privacy.method':
    'حاجب للبيانات على المدخلات والمخرجات للمعرِّفات الخاضعة لقانون حماية البيانات الشخصية، مع استكمال حقول الامتثال في بطاقة النموذج.',
  'fix.security.action': 'التعليمات داخل المحتوى ليست تعليمات',
  'fix.security.method':
    'تدريب على مقاومة حقن التعليمات مع عزل موجِّه النظام، بحيث لا يستطيع نص داخل وثيقة أن يحرف النموذج.',
  'fix.bias.action': 'السؤال نفسه تُجاب عنه الإجابة نفسها',
  'fix.bias.method':
    'تدريب على اتساق الأزواج عبر السمات المحمية التي يسمّيها السجل، مع التقييم على الفارق بين الإجابتين لا على أيٍّ منهما منفردة.',
  'fix.oversight.action': 'مسار إلى موظف بشري وسبب لسلوكه',
  'fix.oversight.method':
    'ربط محفِّزات التصعيد بموظف بشري، وعرضها دون طلب عندما يبدو المواطن في ضائقة، والإفصاح عنها في بطاقة النموذج.',
  'fix.transparency.action': 'يفصح عن ماهيته وعمّا يجهله',
  'fix.transparency.method':
    'الإفصاح عن الهوية عند بدء الجلسة، وذكر درجة عدم اليقين صراحةً في الإجابة لا التلميح إليها بالتحفُّظ.',
  'fix.capability.action': 'إجابات مستندة إلى السجل المنشور',
  'fix.capability.method':
    'إسناد الاسترجاع إلى مجموعة البيانات الحكومية المرتبطة، مع اشتراط أن تحمل الإجابة مصدرها.',
  'fix.redteam.action': 'التحصين ضد المجموعة الخصومية',
  'fix.redteam.method':
    'تدريب خصومي على عائلات الهجمات التي تغطيها مجموعة الفريق الأحمر، مع استبقاء هجمات محجوزة للتشغيل الارتدادي.',

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
  'tour.remediation.title': 'ثم معالجة الفجوات',
  'tour.remediation.body':
    'لا ينتهي الأمر عند الحكم. تقرأ مرحلة المعالجة الفجوات من نتيجة التقييم، وتحدِّد العمل اللازم لسدِّها، وتعرض محاكاةً له، ثم تعيد النسخة المُعاد تدريبها إلى المحرك. والفجوات مقيسة، أما الخطة وإعادة التدريب فمؤشَّرتان بوصفهما إسقاطاً تقديرياً لأن ميزان لا يدرِّب النماذج.',
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
