/**
 * English (en-GB) string catalogue for the MIZAN web shell.
 *
 * Keys established here form the contract that RASHID must implement
 * in ar.ts. Do not add keys in one catalogue without adding them in
 * the other. All values use British English spelling and punctuation.
 */
export const en: Record<string, string> = {
  // Application identity
  'app.name': 'MIZAN',
  'app.tagline': 'Sovereign AI Model Registry and Adaptive Compliance Engine',

  // Navigation
  'nav.registry': 'Registry',
  'nav.evaluate': 'Evaluate',
  'nav.certificates': 'Certificates',
  'nav.about': 'About',

  // Language toggle
  'lang.toggle.label': 'Switch to Arabic',
  'lang.current': 'English',

  // Registry page
  'registry.title': 'Model Registry',
  'registry.subtitle': 'All AI models submitted for government compliance evaluation.',
  'registry.status.pending': 'Pending',
  'registry.status.in_evaluation': 'In Evaluation',
  'registry.status.certified': 'Certified',
  'registry.status.rejected': 'Rejected',
  'registry.empty': 'No models registered yet.',
  'registry.model_id.label': 'Model ID',
  'registry.submitted_at.label': 'Submitted',

  // Model registration
  'model.name.label': 'Model Name',
  'model.endpoint.label': 'Endpoint URL',
  'model.provider.label': 'Provider',
  'model.submit': 'Register Model',

  // Evaluation page
  'evaluation.title': 'Start Evaluation',
  'evaluation.model.label': 'Model',
  'evaluation.use_case.label': 'Use Case',
  'evaluation.submit': 'Begin Evaluation',
  'evaluation.streaming.title': 'Evaluation in Progress',
  'evaluation.streaming.awaiting': 'Awaiting evaluation engine...',
  'evaluation.verdict.certified': 'Certified',
  'evaluation.verdict.rejected': 'Rejected',
  'evaluation.stopping_reason.hoeffding_bound_met': 'Confidence threshold reached',
  'evaluation.stopping_reason.mandatory_control_failed': 'Mandatory control failed',
  'evaluation.stopping_reason.budget_exhausted': 'Evaluation budget exhausted',
  'evaluation.arm_pull.label': 'Engine step',
  'evaluation.confidence.label': 'Confidence',

  // Evidence
  'evidence.probe_id.label': 'Probe',
  'evidence.score.label': 'Score',
  'evidence.passed.yes': 'Passed',
  'evidence.passed.no': 'Failed',

  // Certificate page
  'certificate.title': 'Compliance Certificate',
  'certificate.verdict.certified': 'Certified',
  'certificate.verdict.rejected': 'Rejected',
  'certificate.evidence_hash': 'Evidence Bundle Hash',
  'certificate.issued': 'Issued',
  'certificate.download_pdf': 'Download Certificate PDF',
  'certificate.controls.heading': 'Control Assessments',
  'certificate.model.heading': 'Model Details',
  'certificate.use_case.heading': 'Use Case',
  'certificate.signature.label': 'Digital Signature',
  'certificate.evaluator.label': 'Evaluator',

  // Common
  'common.loading': 'Loading...',
  'common.error': 'An error occurred.',
  'common.back': 'Back',
  'common.view': 'View',
  'common.not_found': 'Not found.',
  'common.retry': 'Retry',
  'common.download': 'Download',
  'common.id.label': 'Identifier',
}
