/**
 * Remediation: what an evaluation found, what would fix it, and what the
 * fixed model would be expected to do.
 *
 * Two halves, and the interface must never let a reader confuse them.
 *
 * The gap analysis is measurement. Every gap below is read from the control
 * states the engine produced and the probes it drew: which mandatory control
 * failed, which was never probed, which passed without earning a bound, and
 * the exact exchange behind each.
 *
 * The remediation plan and the retraining run are projection. MIZAN does not
 * train models and does not observe training. The plan is a rule table from
 * control domain to the work that domain demands, and the projected pass
 * rates are the rates the register requires, not rates anything achieved.
 * Nothing here becomes evidence, and no projection can issue a certificate:
 * only a fresh evaluation of the retrained version can.
 *
 * British English throughout.
 */

import { controlRecord } from './api'
import type { ControlDecision, ProbeStep } from './types'

export type GapKind = 'failing' | 'intermittent' | 'unproven' | 'untested'
export type Severity = 'critical' | 'high' | 'moderate'

export interface Gap {
  controlId: string
  suiteId: string
  kind: GapKind
  severity: Severity
  isMandatory: boolean
  probes: number
  passed: number
  requiredPassRate: number
  achievedBound: number | null
  probesNeeded: number
  /** A probe that failed for this control, when there is one. */
  example: ProbeStep | null
}

export interface Fix {
  id: string
  suiteId: string
  /** Controls this piece of work would settle. */
  controlIds: string[]
  /** Highest severity among the gaps it addresses. */
  severity: Severity
  /** Probes the register requires across the controls in this group. */
  probesRequired: number
  /** Planning estimate for the corpus, at the ratio stated in the interface. */
  corpusItems: number
  /** The pass rate the register requires, which the work must clear. */
  targetPassRate: number
}

/**
 * Items of training data proposed per probe the control set requires.
 *
 * A planning ratio, stated on the panel rather than buried here, and not a
 * measured one. It is deliberately modest: the probe counts the engine
 * derives at a 0.97 confidence threshold run into the hundreds per control,
 * so a generous ratio produces a corpus estimate no one would believe.
 */
export const CORPUS_RATIO = 5

const SEVERITY_ORDER: Record<Severity, number> = { critical: 0, high: 1, moderate: 2 }

/** Suites in the order remediation would sequence them: safety first. */
const SUITE_ORDER = [
  'suite-safety',
  'suite-arabic-linguistic',
  'suite-privacy',
  'suite-security',
  'suite-bias',
  'suite-oversight',
  'suite-transparency',
  'suite-capability',
  'suite-redteam',
]

function severityOf(kind: GapKind, isMandatory: boolean, suiteId: string): Severity {
  if (kind === 'failing') {
    return isMandatory && (suiteId === 'suite-safety' || suiteId === 'suite-privacy')
      ? 'critical'
      : 'high'
  }
  if (kind === 'intermittent') return isMandatory ? 'high' : 'moderate'
  return 'moderate'
}

/**
 * Read the gaps out of one completed evaluation.
 *
 * A certified verdict has gaps too, and usually many: at the present corpus
 * size most controls are settled when the corpus runs out rather than by a
 * bound, and the certificate says so per control. Those are the unproven
 * gaps below.
 */
export function findGaps(
  decisions: Record<string, ControlDecision>,
  steps: ProbeStep[],
): Gap[] {
  const failingExample = new Map<string, ProbeStep>()
  for (const step of steps) {
    if (!step.passed && !failingExample.has(step.control_id)) {
      failingExample.set(step.control_id, step)
    }
  }

  const gaps: Gap[] = []

  for (const [controlId, state] of Object.entries(decisions)) {
    const record = controlRecord(controlId)
    const suiteId = record?.suite_id ?? ''
    const failures = state.n - state.s

    let kind: GapKind | null = null
    if (state.decision === false) {
      kind = 'failing'
    } else if (failures > 0) {
      kind = 'intermittent'
    } else if (state.n === 0) {
      kind = 'untested'
    } else if (state.decision_basis === null || state.decision_basis.startsWith('budget')) {
      kind = 'unproven'
    }

    if (kind === null) continue

    // An advisory control that was simply never probed is not a gap worth
    // putting in front of a reader: it was out of scope for this use case.
    if (kind === 'untested' && !state.is_mandatory) continue

    gaps.push({
      controlId,
      suiteId,
      kind,
      severity: severityOf(kind, state.is_mandatory, suiteId),
      isMandatory: state.is_mandatory,
      probes: state.n,
      passed: state.s,
      requiredPassRate: state.required_pass_rate,
      achievedBound: state.achieved_pass_rate_lower_bound,
      probesNeeded: Math.max(0, state.n_max ?? 0),
      example: failingExample.get(controlId) ?? null,
    })
  }

  gaps.sort((a, b) => {
    const bySeverity = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
    if (bySeverity !== 0) return bySeverity
    if (a.isMandatory !== b.isMandatory) return a.isMandatory ? -1 : 1
    return a.controlId.localeCompare(b.controlId)
  })

  return gaps
}

/**
 * Group gaps into pieces of work.
 *
 * Grouped by suite, because that is the unit a fix is actually bought in:
 * a model does not acquire Arabic refusal behaviour one control at a time.
 */
export function planFixes(gaps: Gap[]): Fix[] {
  const bySuite = new Map<string, Gap[]>()
  for (const gap of gaps) {
    const current = bySuite.get(gap.suiteId) ?? []
    current.push(gap)
    bySuite.set(gap.suiteId, current)
  }

  const fixes: Fix[] = []
  for (const [suiteId, suiteGaps] of bySuite.entries()) {
    const probesRequired = suiteGaps.reduce(
      (total, gap) => total + Math.max(gap.probesNeeded, gap.probes),
      0,
    )
    const severity = suiteGaps
      .map((g) => g.severity)
      .sort((a, b) => SEVERITY_ORDER[a] - SEVERITY_ORDER[b])[0]
    fixes.push({
      id: suiteId,
      suiteId,
      controlIds: suiteGaps.map((g) => g.controlId),
      severity,
      probesRequired,
      corpusItems: probesRequired * CORPUS_RATIO,
      targetPassRate: Math.max(...suiteGaps.map((g) => g.requiredPassRate)),
    })
  }

  fixes.sort((a, b) => {
    const bySeverity = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
    if (bySeverity !== 0) return bySeverity
    return SUITE_ORDER.indexOf(a.suiteId) - SUITE_ORDER.indexOf(b.suiteId)
  })

  return fixes
}

export interface TrainingStage {
  /** Key suffix in the string catalogue: retrain.stage.<key>.title and .body */
  key: string
  /** Share of the run this stage occupies, so the progress bar is not uniform. */
  weight: number
}

/**
 * The stages a remediation cycle would run through.
 *
 * Sequenced the way the work actually depends on itself: nothing can be
 * trained before the corpus exists, and nothing can be re-submitted before
 * the owner's own regression run comes back clean.
 */
export const TRAINING_STAGES: TrainingStage[] = [
  { key: 'corpus', weight: 2 },
  { key: 'alignment', weight: 3 },
  { key: 'guardrails', weight: 2 },
  { key: 'documentation', weight: 1 },
  { key: 'regression', weight: 2 },
]

/** Total weight, so a caller can turn a stage index into a percentage. */
export const TRAINING_WEIGHT = TRAINING_STAGES.reduce((sum, s) => sum + s.weight, 0)
