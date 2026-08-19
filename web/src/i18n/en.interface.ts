/**
 * English (en-GB) strings for the landing page, the platform interface and
 * the guided walkthrough.
 *
 * Kept separate from en.ts so that the Wave 0 shell catalogue, and the
 * Arabic register decisions recorded against it, stay intact. The two
 * catalogues are merged in i18n/index.tsx.
 *
 * Every key added here has a counterpart in ar.interface.ts.
 */
export const enInterface: Record<string, string> = {
  // ---------------------------------------------------------------- landing
  'landing.nav.how': 'How it works',
  'landing.nav.data': 'Government data',
  'landing.nav.usecases': 'Use cases',
  'landing.nav.limits': 'Limits',
  'landing.hero.eyebrow': 'Aligned to the UAE National Strategy for Artificial Intelligence 2031',
  'landing.hero.title': 'Certification for the AI that governments put into service',
  'landing.hero.lede':
    'Nations certify aircraft before they fly and medicines before they ship. MIZAN is the equivalent instrument for an AI model entering government service: a registry, an evaluation engine that stops testing the moment the evidence settles a control, and a signed bilingual certificate that shows its working.',
  'landing.hero.enter': 'Enter MIZAN',
  'landing.hero.tour': 'See how it works',
  'landing.hero.caption': 'No account required. Nothing you submit leaves this machine.',
  'landing.stat.controls': 'Controls in the register',
  'landing.stat.usecases': 'Government use cases',
  'landing.stat.entities': 'Publishing entities',
  'landing.stat.languages': 'Languages, both native',
  'landing.stat.languages.value': 'Arabic and English',

  'landing.what.title': 'What you can do here',
  'landing.what.lede':
    'Four steps, in one sitting. The guided walkthrough inside takes you through them with a worked example.',
  'landing.step.one.title': 'Register a model',
  'landing.step.one.body':
    'Upload a submission file, or fill the short form. The submission carries a model card: what the model is, what it was trained on, whether it touches personal data, and what its owner says its limits are.',
  'landing.step.two.title': 'Choose the use case',
  'landing.step.two.body':
    'A citizen-facing Arabic chatbot is held to a different standard from an internal summarisation tool. Choosing the use case chooses the controls, their weights and the confidence the verdict must reach.',
  'landing.step.three.title': 'Watch the evidence arrive',
  'landing.step.three.body':
    'The engine picks the next test by which one settles the decision fastest, and stops testing a control as soon as it is settled. You see each probe, the answer it drew and the score it earned, as it happens.',
  'landing.step.four.title': 'Read the certificate',
  'landing.step.four.body':
    'Every verdict links to the probe that produced it, and every probe carries a SHA-256 hash. A control that passed without statistical demonstration says so on the certificate face.',

  'landing.principles.title': 'Three commitments',
  'landing.principle.arabic.title': 'Arabic is first-class',
  'landing.principle.arabic.body':
    'Not a translation pass. Suites, attacks, certificates and this interface exist natively in Arabic with correct right-to-left layout. A model that is safe in English and unsafe in Arabic fails.',
  'landing.principle.evidence.title': 'Evidence over assertion',
  'landing.principle.evidence.body':
    'Evidence is append-only, enforced by database triggers and a per-evaluation hash chain rather than by convention, so any edit or excision is detectable by traversal.',
  'landing.principle.limits.title': 'The instrument states its limits',
  'landing.principle.limits.body':
    'A certificate distinguishes a control decided by a confidence bound from one decided when the probe corpus ran out, and prints the bound each control actually earned.',

  'landing.data.title': 'The government data this is grounded in',
  'landing.data.lede':
    'Use cases are bound to real published data, not invented context. Each binding below was fetched and hash-verified, and every field on these cards was read from the manifest that fetch wrote.',
  'landing.data.note':
    'Entity marks below are typographic placeholders drawn by MIZAN, not official emblems. Each card names the publishing entity and links to the portal it publishes through.',
  'landing.data.field.dataset': 'Dataset as published',
  'landing.data.field.portal': 'Portal',
  'landing.data.field.resource': 'Resource identifier',
  'landing.data.field.read': 'Read on',
  'landing.data.field.usecase': 'Grounds',
  'landing.data.open': 'Open the portal',

  'landing.usecases.title': 'Five government use cases',
  'landing.usecases.lede':
    'Each carries its own control set, its own weights and its own confidence threshold, recorded in the published register.',
  'landing.usecases.controls': 'controls',
  'landing.usecases.mandatory': 'mandatory',
  'landing.usecases.threshold': 'Confidence required',

  'landing.limits.title': 'What this is not',
  'landing.limits.body':
    'This is pilot-scale work. The probe corpus is smaller than full statistical backing requires, so many passing controls are decided when the corpus runs out rather than by a confidence bound, and the certificate says so per control. A MIZAN certificate records conformance with the MIZAN control set. It is not a legal opinion, and it is not approval by any government entity.',
  'landing.footer.note': 'Sovereign AI evaluation registry. Proprietary, all rights reserved.',

  // --------------------------------------------------------------- platform
  'console.back': 'Back to the introduction',
  'console.guide': 'Guide',
  'console.guide.restart': 'Restart the walkthrough',
  'console.mode.live': 'Connected to the evaluation engine',
  'console.mode.recorded': 'Replaying a recorded run',
  'console.mode.recorded.detail':
    'No engine is reachable from this page, so MIZAN replays evaluations that the real engine recorded against the real probe corpus. Every step, verdict and hash shown was produced by the engine.',
  'console.mode.live.detail':
    'This page is talking to a MIZAN API. Evaluations you start run for real and write evidence to the registry.',

  'console.step.submit': 'Submit',
  'console.step.usecase': 'Use case',
  'console.step.evaluate': 'Evaluate',
  'console.step.certificate': 'Certificate',
  'console.step.of': 'Step {n} of 4',

  'submit.title': 'Submit a model for evaluation',
  'submit.lede':
    'Drop a submission file below. A submission is a small JSON file: who made the model, what it is, and the model card its owner stands behind.',
  'submit.drop': 'Drop a submission file here',
  'submit.browse': 'or choose a file',
  'submit.samples.title': 'No file to hand? Take one of these.',
  'submit.samples.lede':
    'Three prepared submissions, each of which behaves differently under evaluation. Download one, then drop it above.',
  'submit.sample.compliant.name': 'Compliant Arabic assistant',
  'submit.sample.compliant.detail': 'A complete model card and a model that answers safely in both languages. Expect a certificate.',
  'submit.sample.non_compliant.name': 'Unsafe multilingual model',
  'submit.sample.non_compliant.detail': 'Refuses benign questions, and complies with harmful Arabic requests. Expect an early rejection.',
  'submit.sample.incomplete.name': 'Undocumented model',
  'submit.sample.incomplete.detail': 'A capable model with a thin model card. Expect documentary controls to fail.',
  'submit.sample.download': 'Download',
  'submit.file.accepted': 'Submission read',
  'submit.file.rejected': 'That file could not be read as a MIZAN submission.',
  'submit.field.provider': 'Provider',
  'submit.field.version': 'Version',
  'submit.field.served': 'Served by',
  'submit.served.mock': 'Deterministic mock adapter, {profile} profile',
  'submit.served.endpoint': 'Live endpoint',
  'submit.register': 'Register this model',
  'submit.registered': 'Registered',
  'submit.registry.title': 'Registry',
  'submit.registry.lede': 'Models submitted to this registry.',

  'usecase.title': 'Choose the use case it is intended for',
  'usecase.lede':
    'This is the consequential choice. It fixes which controls apply, how heavily each weighs, and how much confidence the verdict must reach before a certificate can be issued.',
  'usecase.selected': 'Selected',
  'usecase.select': 'Select',
  'usecase.datasets': 'Grounded in data published by',

  'evaluate.title': 'Adjudication',
  'evaluate.lede':
    'The engine chooses the next probe by which one settles the decision fastest, and retires a control the moment its evidence settles it.',
  'evaluate.start': 'Start the evaluation',
  'evaluate.restart': 'Run it again',
  'evaluate.running': 'Evaluation running',
  'evaluate.complete': 'Evaluation complete',
  'evaluate.speed': 'Speed',
  'evaluate.speed.steady': 'Steady',
  'evaluate.speed.fast': 'Fast',
  'evaluate.probes': 'Probes conducted',
  'evaluate.controls.settled': 'Controls with evidence',
  'evaluate.stream.title': 'Probe stream',
  'evaluate.stream.empty': 'The stream fills as the engine draws probes.',
  'evaluate.controls.title': 'Control board',
  'evaluate.controls.hint': 'Select any control to read the exchange behind it.',
  'evaluate.passed': 'Passed',
  'evaluate.failed': 'Failed',
  'evaluate.awaiting': 'Awaiting evidence',
  'evaluate.stopped.corpus_exhausted': 'Stopped: the probe corpus ran out',
  'evaluate.stopped.mandatory_control_failed': 'Stopped: a mandatory control failed',
  'evaluate.stopped.hoeffding_bound_met': 'Stopped: every mandatory control was settled',
  'evaluate.stopped.budget_exhausted': 'Stopped: the probe budget was spent',
  'evaluate.verdict.certified': 'Certified',
  'evaluate.verdict.rejected': 'Not certified',
  'evaluate.view.certificate': 'Open the certificate',

  'evidence.title': 'The exchange behind this score',
  'evidence.prompt': 'Probe',
  'evidence.response': 'Model response',
  'evidence.response.attestation': 'Decided on the model card rather than by a probe.',
  'evidence.scorer': 'Scorer',
  'evidence.score': 'Score',
  'evidence.hash': 'Evidence hash (SHA-256)',
  'evidence.control': 'Control',
  'evidence.close': 'Close',
  'evidence.empty': 'Select a probe in the stream to open it here.',

  'cert.title': 'Certificate',
  'cert.none': 'A certificate appears here once an evaluation reaches a verdict.',
  'cert.tier.statistical': 'Statistical tier: every mandatory control earned a confidence bound.',
  'cert.tier.budget': 'Budget tier: one or more mandatory controls were settled without a confidence bound. Each is marked below.',
  'cert.model': 'Model',
  'cert.usecase': 'Use case',
  'cert.issued': 'Issued',
  'cert.bundle': 'Evidence bundle hash',
  'cert.signature': 'Signature',
  'cert.controls': 'Control results',
  'cert.control.basis': 'Decision basis',
  'cert.control.probes': 'Probes',
  'cert.control.bound': 'Lower bound earned',
  'cert.control.required': 'Required',
  'cert.datasets': 'Datasets consulted',
  'cert.asserts': 'What this certificate asserts',
  'cert.does_not': 'What it does not assert',
  'cert.validity': 'Validity',
  'cert.download': 'Download the certificate as JSON',
  'cert.print': 'Print',
  'cert.served': 'Evaluation served by',

  // ------------------------------------------------------------ walkthrough
  'tour.next': 'Next',
  'tour.back': 'Back',
  'tour.skip': 'Skip the walkthrough',
  'tour.done': 'Start using it',
  'tour.progress': '{n} of {total}',
  'tour.welcome.title': 'Welcome to MIZAN',
  'tour.welcome.body':
    'This walkthrough takes about a minute. It shows you how a model goes from a submission file to a signed certificate. You can leave it at any point and pick it up again from the Guide button.',
  'tour.submit.title': 'Start with a submission',
  'tour.submit.body':
    'Download one of the prepared submissions and drop it in the panel. If you want the happy path, take the compliant Arabic assistant.',
  'tour.registry.title': 'The registry',
  'tour.registry.body':
    'Everything submitted here appears in the registry with its lifecycle state: pending, in evaluation, certified or not certified.',
  'tour.usecase.title': 'The use case decides the standard',
  'tour.usecase.body':
    'Pick the use case the model is intended for. A citizen-facing Arabic chatbot demands the broadest control set and the highest confidence of the five.',
  'tour.evaluate.title': 'Watch it adjudicate',
  'tour.evaluate.body':
    'Start the evaluation. Probes arrive on the left, controls settle on the right. Nothing is precomputed: each control is retired the moment its evidence settles it.',
  'tour.evidence.title': 'Open any probe',
  'tour.evidence.body':
    'Select a probe in the stream, or a control on the board, to read the exact prompt, the answer the model gave and the hash of the record.',
  'tour.certificate.title': 'The certificate',
  'tour.certificate.body':
    'When the verdict lands, the certificate is issued in both languages, control by control, with the statistical strength each control actually earned.',

  // ------------------------------------------------------------------ misc
  'common.close': 'Close',
  'common.optional': 'Optional',
  'common.mandatory': 'Mandatory',
  'common.advisory': 'Advisory',
  'common.probes': 'probes',
  'common.step': 'Step',
  'common.continue': 'Continue',
}
