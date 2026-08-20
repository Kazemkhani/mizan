/**
 * Shared shapes for the MIZAN interface.
 *
 * The interface runs in two modes against the same shapes: connected to a
 * MIZAN API, or replaying runs the engine recorded into
 * data/recorded_runs.json. Every field below exists in both, so no
 * component needs to know which mode it is in.
 */

export type Locale = 'en' | 'ar'
export type Mode = 'live' | 'recorded'
export type Verdict = 'certified' | 'rejected'
export type Profile = 'compliant' | 'non_compliant'

export interface UseCase {
  id: string
  name_en: string
  name_ar: string
  description_en: string
  description_ar: string
  use_case_class: string
  confidence_threshold: number
  controls?: UseCaseControl[]
  weighting_rationale?: string
}

export interface UseCaseControl {
  control_id: string
  name_en: string
  name_ar: string
  framework_clause: string
  is_mandatory: boolean
  weight: number
  suite_id: string
}

export interface ControlRecord {
  id: string
  name_en: string
  name_ar: string
  description_en: string
  description_ar: string
  domain_label_en: string
  domain_label_ar: string
  suite_id: string
  framework_clause: string
  pass_threshold: number
  severity: string
}

export interface DatasetBinding {
  use_case_id: string
  dataset_id: string
  title: string
  publisher: string
  portal: string
  portal_url: string
  page_url: string
  resource_guid: string
  read_date: string
  last_modified: string
  cache_sha256: string
}

export interface ModelRow {
  id: string
  name_en: string
  name_ar: string
  provider: string
  version: string
  status: 'pending' | 'in_evaluation' | 'certified' | 'rejected'
  submitted_at: string
}

/** One probe drawn by the engine, as the stream and the replay both report it. */
export interface ProbeStep {
  step: number
  suite_id: string
  control_id: string
  probe_id: string
  passed: boolean
  score: number
  locale: string
  prompt: string
  response: string
  scorer: string
  evidence_type: string
  payload_hash: string
}

export interface ControlDecision {
  n: number
  s: number
  p_hat: number
  required_pass_rate: number
  is_mandatory: boolean
  is_zero_tolerance: boolean
  decided: boolean
  decision: boolean | null
  decision_basis: string | null
  achieved_pass_rate_lower_bound: number | null
  violation_rate_bound: number | null
  /** Probes this control needs at the declared confidence, from the engine. */
  n_max?: number
}

export interface CertificateControlResult {
  control_id: string
  name_en: string
  name_ar: string
  domain_label_en: string
  domain_label_ar: string
  framework_clause: string
  severity: string
  is_mandatory: boolean
  decision: boolean | null
  decision_basis: string | null
  basis_labels: { label_en: string; label_ar: string; register: string }
  statistically_decided: boolean
  probes_conducted: number
  probes_passed: number
  required_pass_rate: number | null
  achieved_pass_rate_lower_bound: number | null
  violation_rate_bound: number | null
}

export interface CertificateData {
  title_en: string
  title_ar: string
  issuing_authority_en: string
  issuing_authority_ar: string
  verdict: Verdict
  headline_en: string
  headline_ar: string
  body_en: string
  body_ar: string
  evidence_tier: 'statistical' | 'budget'
  model: { id: string; name_en: string; name_ar: string; provider: string; version: string }
  use_case: { id: string; name_en: string; name_ar: string; confidence_threshold: number | null }
  control_set_version: string
  control_results: CertificateControlResult[]
  mandatory_controls: number
  controls_statistically_decided: number
  controls_budget_decided: number
  controls_undecided?: number
  probes_conducted: number
  stopping_reason: string | null
  datasets_consulted: DatasetBinding[]
  evaluation_served_by: { kind: string; detail: string | null }
  validity_en: string
  validity_ar: string
  asserts_en: string[]
  asserts_ar: string[]
  does_not_assert_en: string[]
  does_not_assert_ar: string[]
  signature_note_en: string
  signature_note_ar: string
}

export interface Certificate {
  id: string
  evaluation_id: string
  model_id: string
  use_case_id: string
  verdict: Verdict
  evidence_bundle_hash: string
  certificate_data: CertificateData
  signature: string | null
  issued_at: string
  pdf_path: string | null
}

/** A submission file, as uploaded or as filled in by the form. */
export interface Submission {
  name_en: string
  name_ar: string
  provider: string
  version: string
  endpoint_url: string | null
  evaluation_profile: Profile
  model_card: Record<string, unknown>
}

export interface RecordedRun {
  run_id: string
  submission_id: string
  submission_name_en: string
  submission_name_ar: string
  provider: string
  version: string
  use_case_id: string
  profile: Profile
  verdict: Verdict
  stopping_reason: string
  total_queries: number
  arm_pull_count: number
  steps: ProbeStep[]
  control_decisions: Record<string, ControlDecision>
  certificate: Certificate
}

export interface SampleSubmission {
  submission_id: string
  name_en: string
  name_ar: string
  provider: string
  version: string
  profile: Profile
}

export interface RecordedDocument {
  generated_at: string
  generated_by: string
  note: string
  submissions: SampleSubmission[]
  use_cases: UseCase[]
  controls: ControlRecord[]
  datasets: DatasetBinding[]
  runs: RecordedRun[]
}
