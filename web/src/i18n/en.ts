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

  // Evaluation page
  'evaluation.title': 'Start Evaluation',
  'evaluation.model.label': 'Model',
  'evaluation.use_case.label': 'Use Case',
  'evaluation.submit': 'Begin Evaluation',
  'evaluation.streaming.title': 'Evaluation in Progress',
  'evaluation.streaming.awaiting': 'Awaiting evaluation engine...',

  // Certificate page
  'certificate.title': 'Compliance Certificate',
  'certificate.verdict.certified': 'Certified',
  'certificate.verdict.rejected': 'Rejected',
  'certificate.evidence_hash': 'Evidence Bundle Hash',
  'certificate.issued': 'Issued',
  'certificate.download_pdf': 'Download Certificate PDF',

  // Common
  'common.loading': 'Loading...',
  'common.error': 'An error occurred.',
  'common.back': 'Back',
  'common.view': 'View',
}
