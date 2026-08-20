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
    'You are watching a recorded assessment. MIZAN really ran these checks; this page replays the saved result rather than running them again now. Nothing shown here was written by hand.',
  'console.mode.live.detail':
    'This page is talking to a MIZAN API. Evaluations you start run for real and write evidence to the registry.',

  'console.step.submit': 'Submit',
  'console.step.usecase': 'Use case',
  'console.step.evaluate': 'Evaluate',
  'console.step.certificate': 'Certificate',
  'console.step.remediate': 'Remediation',
  'console.step.of': 'Step {n} of 5',

  'submit.title': 'Submit a model for evaluation',
  'submit.lede':
    'Drop a submission file below. A submission is a small JSON file: who made the model, what it is, and the model card its owner stands behind.',
  'submit.drop': 'Drop a submission file here',
  'submit.browse': 'or choose a file',
  'submit.samples.title': 'No file to hand? Take one of these.',
  'submit.samples.lede':
    'Three prepared submissions, each of which behaves differently under evaluation. Load one straight into the panel, or download the file and drop it back in.',
  'submit.sample.compliant.name': 'Compliant Arabic assistant',
  'submit.sample.compliant.detail': 'A complete model card and a model that answers safely in both languages. Expect a certificate.',
  'submit.sample.non_compliant.name': 'Unsafe multilingual model',
  'submit.sample.non_compliant.detail': 'Refuses benign questions, and complies with harmful Arabic requests. Expect an early rejection.',
  'submit.sample.incomplete.name': 'Undocumented model',
  'submit.sample.incomplete.detail': 'A capable model with a thin model card. Expect documentary controls to fail.',
  'submit.sample.use': 'Load this one',
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

  'evaluate.title': 'Assessment',
  'evaluate.lede':
    'The engine runs checks against the model one at a time. It picks the check most likely to settle each standard fastest, and stops testing a standard the moment it has enough evidence.',
  'evaluate.start': 'Start the evaluation',
  'evaluate.restart': 'Run it again',
  'evaluate.running': 'Evaluation running',
  'evaluate.complete': 'Evaluation complete',
  'evaluate.speed': 'Speed',
  'evaluate.speed.steady': 'Steady',
  'evaluate.speed.fast': 'Fast',
  'evaluate.probes': 'Checks performed',
  'evaluate.controls.settled': 'Standards assessed',
  'evaluate.stream.title': 'Verification log',
  'evaluate.stream.empty': 'Checks appear here as the evaluation runs.',
  'evaluate.controls.title': 'Standards status',
  'evaluate.controls.hint': 'Select any standard to read the check behind it.',
  'evaluate.passed': 'Passed',
  'evaluate.failed': 'Failed',
  'evaluate.awaiting': 'Awaiting evidence',
  'evaluate.stopped.corpus_exhausted': 'Evaluation complete: all available tests were conducted',
  'evaluate.stopped.mandatory_control_failed': 'Stopped: a required standard was not met',
  'evaluate.stopped.hoeffding_bound_met': 'Evaluation complete: all required standards reached the declared confidence',
  'evaluate.stopped.budget_exhausted': 'Evaluation complete: the test allocation was spent',
  'evaluate.verdict.certified': 'Certified',
  'evaluate.verdict.rejected': 'Not certified',
  'evaluate.view.certificate': 'Open the certificate',
  'evaluate.view.remediation': 'Close the gaps',

  'evidence.title': 'The exchange behind this score',
  'evidence.prompt': 'Check',
  'evidence.response': 'Model response',
  'evidence.response.attestation': 'Decided from the model card, not from a live check.',
  'evidence.scorer': 'How this was marked',
  'evidence.score': 'Score',
  'evidence.hash': 'Evidence hash (SHA-256)',
  'evidence.control': 'Standard',
  'evidence.close': 'Close',
  'evidence.empty': 'Select a check from the verification log to read its full record here.',

  'cert.title': 'Certificate',
  'cert.none': 'A certificate appears here once the assessment reaches a decision.',
  'cert.tier.statistical': 'Confirmed by evidence: every required standard reached the declared certainty.',
  'cert.tier.budget': 'Not enough checks to confirm: one or more required standards ran out of checks before certainty was reached. Each is marked below.',
  'cert.model': 'Model',
  'cert.usecase': 'Use case',
  'cert.issued': 'Issued',
  'cert.bundle': 'Evidence bundle hash',
  'cert.signature': 'Signature',
  'cert.controls': 'Standard results',
  'cert.control.basis': 'How this was decided',
  'cert.control.probes': 'Checks',
  'cert.control.bound': 'Certainty reached',
  'cert.control.required': 'Required',
  'cert.datasets': 'Datasets consulted',
  'cert.asserts': 'What this certificate asserts',
  'cert.does_not': 'What it does not assert',
  'cert.validity': 'Validity',
  'cert.download': 'Download the certificate as JSON',
  'cert.print': 'Print',
  'cert.served': 'Evaluation served by',

  // -------------------------------------------------------- remediation
  'remediate.eyebrow': 'After the decision',
  'remediate.title': 'Close the gaps and come back',
  'remediate.lede':
    'Every model arrives with gaps, including one that certifies. This stage reads those gaps out of the run, sets out the work that would close them, rehearses that work, and hands the retrained version back to the engine.',
  'remediate.none': 'Run an evaluation first. The gaps are read out of its result.',
  'remediate.phase.gaps': 'Gaps found',
  'remediate.phase.plan': 'Work required',
  'remediate.phase.training': 'Retraining',
  'remediate.phase.ready': 'Back to the engine',
  'remediate.projection': 'Projection. Nothing on this panel is evidence, and none of it can issue a certificate.',
  'remediate.simulated': 'Simulated run. MIZAN does not train models and does not observe training. This rehearses the sequence a remediation cycle follows.',
  'remediate.gaps.measured': 'Measured. Every figure below was read from the standard results and the checks the engine ran.',
  'remediate.gaps.total': 'Gaps found',
  'remediate.gaps.failing': 'Failing behaviour',
  'remediate.gaps.unproven': 'Unconfirmed standards',
  'remediate.gaps.mandatory': 'Mandatory among them',
  'remediate.gaps.next': 'See the work required',
  'remediate.gap.needs': 'Checks needed',
  'remediate.gap.open': 'Open the exchange',
  'remediate.kind.failing': 'Failed',
  'remediate.kind.intermittent': 'Intermittent',
  'remediate.kind.unproven': 'Not demonstrated',
  'remediate.kind.untested': 'Never checked',
  'remediate.reading.failing':
    'The model did not meet this standard. The behaviour has to change before a certificate is possible.',
  'remediate.reading.intermittent':
    'The model passed most checks and failed some. An intermittent failure on a required standard is a failure.',
  'remediate.reading.unproven':
    'No violation was observed, but the available checks ran out before the required certainty was reached. The behaviour may be sound; the evidence is not yet there.',
  'remediate.reading.untested':
    'This standard was not checked in this assessment. Nothing is known about it either way.',
  'remediate.severity.critical': 'Critical',
  'remediate.severity.high': 'High',
  'remediate.severity.moderate': 'Moderate',
  'remediate.plan.lede':
    'One piece of work per standard domain, because that is the unit a fix is bought in: a model does not acquire Arabic refusal behaviour one standard at a time. Check counts are planning estimates at {ratio} items per check the register requires, {items} items in total.',
  'remediate.plan.next': 'Run the retraining',
  'remediate.fix.controls': 'Standards it would settle',
  'remediate.fix.probes': 'Checks required',
  'remediate.fix.corpus': 'Training checks proposed',
  'remediate.fix.target': 'Rate it must clear',
  'remediate.fix.source':
    'Drawn from the government data bound to {useCase}, so the vocabulary and register match what the model will meet in service.',
  'remediate.uplift.title': 'Where the work would land',
  'remediate.uplift.lede':
    'Observed rate against the rate the register requires. The second figure is the requirement, not a result: only a fresh evaluation can say what the retrained version achieves.',
  'remediate.handback.title': 'Back to the engine',
  'remediate.handback.body':
    'A projection cannot certify anything. Submit the retrained version as a new version and let the engine assess it: a certificate is valid for the exact version assessed, so a retrained model is a new submission, not an amendment to the old one.',
  'remediate.handback.action': 'Submit the retrained version',
  'remediate.rerun.note':
    'Re-evaluating the retrained version. It carries the fixes set out in the remediation plan.',

  'retrain.progress': 'Stage {n} of {total}, {percent}% complete',
  'retrain.stage.corpus.title': 'Assemble the corpus',
  'retrain.stage.corpus.body':
    'Author {items} items across the domains that failed, in Arabic natively where the control is Arabic, and hold back a fifth of them so the regression run is not scored on what was trained on.',
  'retrain.stage.corpus.done': 'corpus assembled, held-out split reserved',
  'retrain.stage.alignment.title': 'Alignment passes',
  'retrain.stage.alignment.body':
    'Fine-tune {model} on the assembled corpus, checking after each pass that behaviour outside the targeted domains has not moved.',
  'retrain.stage.alignment.done': 'alignment passes complete, no regression outside the targets',
  'retrain.stage.guardrails.title': 'Guard rails and system prompt',
  'retrain.stage.guardrails.body':
    'Wire the changes that do not belong in weights: refusal routing, the escalation path to a human agent, personal data redaction, and identity disclosure at the opening of a session.',
  'retrain.stage.guardrails.done': 'guard rails wired, escalation path tested',
  'retrain.stage.documentation.title': 'Model card',
  'retrain.stage.documentation.body':
    'Complete the fields the documentary controls read. A control decided on the model card fails on an empty field however the model behaves.',
  'retrain.stage.documentation.done': 'model card completed against the documentary controls',
  'retrain.stage.regression.title': 'The owner\u2019s own regression run',
  'retrain.stage.regression.body':
    'Run the {fixes} pieces of work against the held-out split before submitting anything, so MIZAN is not the first party to see a failure.',
  'retrain.stage.regression.done': 'regression clean on the held-out split, ready to submit',

  'fix.safety.action': 'Harmful request refusal, in both languages',
  'fix.safety.method':
    'Refusal training on an adversarial set authored natively in Arabic and English, with the refusal required to hold under rephrasing and role play.',
  'fix.arabic_linguistic.action': 'Arabic answered in Arabic, in the government register',
  'fix.arabic_linguistic.method':
    'Instruction data written natively in Modern Standard Arabic using published government vocabulary. Translated items are excluded: a translated refusal set is what produced this gap.',
  'fix.privacy.action': 'Personal data never echoed or retained',
  'fix.privacy.method':
    'Redaction guard on input and output for identifiers under the Personal Data Protection Law, plus the compliance fields on the model card.',
  'fix.security.action': 'Instructions in content are not instructions',
  'fix.security.method':
    'Prompt injection resistance training with system prompt isolation, so text inside a document cannot redirect the model.',
  'fix.bias.action': 'The same question answered the same way',
  'fix.bias.method':
    'Paired prompt consistency training across the protected attributes the register names, scored on the difference between the two answers rather than on either alone.',
  'fix.oversight.action': 'A route to a human, and a reason to take it',
  'fix.oversight.method':
    'Escalation triggers wired to a human agent, offered without being asked for when a citizen is in distress, and declared on the model card.',
  'fix.transparency.action': 'Says what it is and what it does not know',
  'fix.transparency.method':
    'Identity disclosure at the opening of a session, and uncertainty stated in the answer rather than implied by hedging.',
  'fix.capability.action': 'Answers grounded in the published record',
  'fix.capability.method':
    'Retrieval grounding on the bound government dataset, with the answer required to carry what it was drawn from.',
  'fix.redteam.action': 'Hardening against the adversarial set',
  'fix.redteam.method':
    'Adversarial training on the attack families the red team suite covers, with the held-out attacks kept back for the regression run.',

  // ------------------------------------------------------------ walkthrough
  'tour.next': 'Next',
  'tour.back': 'Back',
  'tour.skip': 'Skip the walkthrough',
  'tour.done': 'Start using it',
  'tour.running': 'Assessment running...',
  'tour.run_again': 'Run it again',
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
  'tour.evaluate.title': 'Watch the assessment run',
  'tour.evaluate.body':
    'Press Start. Checks arrive on the left; standards settle on the right. Nothing is precomputed: each standard is retired the moment the engine has enough evidence.',
  'tour.evidence.title': 'Open any check',
  'tour.evidence.body':
    'Select any check in the verification log, or any standard on the board, to read the exact prompt, the answer the model gave, and the fingerprint of the record.',
  'tour.remediation.title': 'Then close the gaps',
  'tour.remediation.body':
    'A decision is not the end. The remediation stage reads the gaps out of the run, sets out the work that would close them, rehearses it, and sends the retrained version back through the engine. The gaps are measured; the plan and the retraining are marked as projection, because MIZAN does not train models.',
  'tour.certificate.title': 'The certificate',
  'tour.certificate.body':
    'When the decision lands, the certificate is issued in both languages, standard by standard, with the certainty each standard actually reached.',

  // ------------------------------------------------------------------ misc
  'skiplink': 'Skip to main content',
  'common.close': 'Close',
  'common.optional': 'Optional',
  'common.mandatory': 'Mandatory',
  'common.advisory': 'Advisory',
  'common.probes': 'checks',
  'common.step': 'Step',
  'common.continue': 'Continue',
}
