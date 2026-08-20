/**
 * The interface's data layer.
 *
 * Two modes, one set of functions:
 *
 *   live      a MIZAN API answered the health check. Models are registered
 *             for real, evaluations run for real, and probes arrive over a
 *             websocket as the engine draws them.
 *
 *   recorded  no API answered. The catalogue and the evaluations come from
 *             data/recorded_runs.json, which scripts/export_demo_runs.py
 *             produced by running the real engine against the real corpus.
 *             The replay is paced so a reader can follow it; nothing about
 *             the outcome is invented.
 *
 * The mode is detected once, at start-up, and reported in the interface
 * rather than hidden.
 */

import recorded from '../data/recorded_runs.json'
import type {
  Certificate,
  ControlDecision,
  DatasetBinding,
  Mode,
  ModelRow,
  ProbeStep,
  Profile,
  RecordedDocument,
  RecordedRun,
  Submission,
  UseCase,
} from './types'

const RECORDED = recorded as unknown as RecordedDocument

const API_BASE = '/api/v1'
const HEALTH_TIMEOUT_MS = 1500

export interface EvaluationOutcome {
  verdict: 'certified' | 'rejected'
  stopping_reason: string
  control_decisions: Record<string, ControlDecision>
  certificate: Certificate | null
}

export interface RunHandle {
  cancel: () => void
  /**
   * For recorded runs only. Cancels any remaining step animation and emits
   * onDone immediately with the pre-loaded result. Used by the guided tour to
   * settle to a final state before spotlighting the certificate or remediation
   * panel, without making the reader wait through the full animation.
   *
   * Has no effect on live evaluations (the result genuinely does not exist
   * yet). On a live run the caller should gate advancement instead.
   */
  flush?: () => void
}

/** Detect whether an engine is reachable. Never throws. */
export async function detectMode(): Promise<Mode> {
  if (typeof window === 'undefined') return 'recorded'
  try {
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS)
    const response = await fetch(`${API_BASE}/health`, { signal: controller.signal })
    window.clearTimeout(timer)
    if (!response.ok) return 'recorded'
    const body = (await response.json()) as { status?: string }
    return body.status === 'ok' ? 'live' : 'recorded'
  } catch {
    return 'recorded'
  }
}

// ---------------------------------------------------------------- catalogue

export function recordedDocument(): RecordedDocument {
  return RECORDED
}

export async function fetchUseCases(mode: Mode): Promise<UseCase[]> {
  if (mode === 'live') {
    try {
      const response = await fetch(`${API_BASE}/use-cases`)
      if (response.ok) return (await response.json()) as UseCase[]
    } catch {
      // Fall through to the recorded catalogue.
    }
  }
  return RECORDED.use_cases
}

export async function fetchDatasets(mode: Mode): Promise<DatasetBinding[]> {
  if (mode === 'live') {
    try {
      const response = await fetch(`${API_BASE}/datasets`)
      if (response.ok) return (await response.json()) as DatasetBinding[]
    } catch {
      // Fall through to the recorded bindings.
    }
  }
  return RECORDED.datasets
}

export async function fetchModels(mode: Mode): Promise<ModelRow[]> {
  if (mode === 'live') {
    try {
      const response = await fetch(`${API_BASE}/models`)
      if (response.ok) return (await response.json()) as ModelRow[]
    } catch {
      // Fall through to an empty registry.
    }
  }
  return []
}

/** Controls a use case demands, resolved against the control register. */
export function controlsFor(useCaseId: string): string[] {
  const run = RECORDED.runs.find((r) => r.use_case_id === useCaseId)
  if (run === undefined) return []
  return Object.keys(run.control_decisions)
}

export function controlRecord(controlId: string) {
  return RECORDED.controls.find((c) => c.id === controlId)
}

// --------------------------------------------------------------- submission

export async function registerModel(mode: Mode, submission: Submission): Promise<string> {
  if (mode === 'live') {
    const response = await fetch(`${API_BASE}/models`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(submission),
    })
    if (!response.ok) {
      throw new Error(`Registration failed with status ${response.status}.`)
    }
    const body = (await response.json()) as { id: string }
    return body.id
  }
  // In replay the registry is local to the page.
  return `local-${Date.now().toString(36)}`
}

// --------------------------------------------------------------- evaluation

interface RunCallbacks {
  onStep: (step: ProbeStep) => void
  onDone: (outcome: EvaluationOutcome) => void
  onError: (message: string) => void
}

/**
 * Start an evaluation and report progress.
 *
 * In live mode this posts an evaluation, opens the stream, and forwards
 * each arm pull. In recorded mode it replays the run recorded for this use
 * case and profile at the requested pace.
 */
export function startEvaluation(
  mode: Mode,
  options: {
    modelId: string
    useCaseId: string
    profile: Profile
    submissionId: string | null
    stepDelayMs: number
  },
  callbacks: RunCallbacks,
): RunHandle {
  if (mode === 'live') {
    return startLiveEvaluation(options, callbacks)
  }
  return startRecordedEvaluation(options, callbacks)
}

/**
 * Pick the recorded run to replay.
 *
 * A submission downloaded from this interface matches a run exactly,
 * because the runs were recorded from those same files. Any other
 * submission falls back to the recorded run whose declared profile matches,
 * and the interface says so rather than implying the upload itself was
 * evaluated.
 */
export function findRun(
  useCaseId: string,
  profile: Profile,
  submissionId: string | null,
): RecordedRun | undefined {
  if (submissionId !== null) {
    const exact = RECORDED.runs.find(
      (r) => r.use_case_id === useCaseId && r.submission_id === submissionId,
    )
    if (exact !== undefined) return exact
  }
  return (
    RECORDED.runs.find((r) => r.use_case_id === useCaseId && r.profile === profile) ??
    RECORDED.runs.find((r) => r.use_case_id === useCaseId)
  )
}

function startRecordedEvaluation(
  options: { useCaseId: string; profile: Profile; submissionId: string | null; stepDelayMs: number },
  callbacks: RunCallbacks,
): RunHandle {
  const run = findRun(options.useCaseId, options.profile, options.submissionId)
  if (run === undefined) {
    callbacks.onError('No recorded run exists for that use case.')
    return { cancel: () => undefined }
  }

  let index = 0
  let cancelled = false
  let timer = 0

  const tick = () => {
    if (cancelled) return
    if (index >= run.steps.length) {
      callbacks.onDone({
        verdict: run.verdict,
        stopping_reason: run.stopping_reason,
        control_decisions: run.control_decisions,
        certificate: run.certificate,
      })
      return
    }
    callbacks.onStep(run.steps[index])
    index += 1
    timer = window.setTimeout(tick, options.stepDelayMs)
  }

  timer = window.setTimeout(tick, options.stepDelayMs)

  return {
    cancel: () => {
      cancelled = true
      window.clearTimeout(timer)
    },
    flush: () => {
      if (cancelled) return
      cancelled = true
      window.clearTimeout(timer)
      callbacks.onDone({
        verdict: run.verdict,
        stopping_reason: run.stopping_reason,
        control_decisions: run.control_decisions,
        certificate: run.certificate,
      })
    },
  }
}

function startLiveEvaluation(
  options: { modelId: string; useCaseId: string; stepDelayMs: number },
  callbacks: RunCallbacks,
): RunHandle {
  let socket: WebSocket | null = null
  let cancelled = false
  let settled = false
  let polling = false
  // The engine outruns a reader, so live steps are queued and released at
  // the same pace as a replay. The evaluation itself is never slowed.
  const queue: ProbeStep[] = []
  const steps: ProbeStep[] = []
  let draining = false
  let pending: EvaluationOutcome | null = null

  const drain = () => {
    if (cancelled) return
    draining = true
    const next = queue.shift()
    if (next !== undefined) {
      steps.push(next)
      callbacks.onStep(next)
      window.setTimeout(drain, options.stepDelayMs)
      return
    }
    draining = false
    if (pending !== null) {
      const outcome = pending
      pending = null
      callbacks.onDone(outcome)
    }
  }

  const run = async () => {
    try {
      const created = await fetch(`${API_BASE}/evaluations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: options.modelId, use_case_id: options.useCaseId }),
      })
      if (!created.ok) {
        callbacks.onError(`The engine refused the evaluation (status ${created.status}).`)
        return
      }
      const evaluation = (await created.json()) as { id: string }
      if (cancelled) return

      const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${scheme}://${window.location.host}${API_BASE}/ws/evaluations/${evaluation.id}/stream`
      socket = new WebSocket(url)

      socket.onmessage = (event: MessageEvent<string>) => {
        const message = JSON.parse(event.data) as {
          event_type: string
          payload: Record<string, unknown>
        }
        if (message.event_type === 'arm_pull') {
          const p = message.payload
          if (typeof p.probe_id !== 'string' || p.probe_id === '') return
          queue.push({
            step: Number(p.step ?? 0),
            suite_id: String(p.suite_id ?? ''),
            control_id: String(p.control_id ?? ''),
            probe_id: String(p.probe_id),
            passed: Boolean(p.passed),
            score: Number(p.score ?? p.reward ?? 0),
            locale: String(p.locale ?? 'en'),
            prompt: String(p.prompt ?? ''),
            response: String(p.response ?? ''),
            scorer: String(p.scorer ?? ''),
            evidence_type: String(p.evidence_type ?? 'probe_result'),
            payload_hash: String(p.payload_hash ?? ''),
          })
          if (!draining) drain()
        } else if (message.event_type === 'stop') {
          const p = message.payload
          void finish(evaluation.id, p)
        } else if (message.event_type === 'error') {
          callbacks.onError(String(message.payload.message ?? 'The engine reported an error.'))
        }
      }

      // A proxy that does not forward the websocket upgrade leaves the
      // evaluation running with nothing reported. Rather than showing an
      // empty stream, fall back to polling the evaluation and reading its
      // evidence when the socket does not deliver.
      socket.onerror = () => {
        void pollUntilDone(evaluation.id)
      }
      socket.onclose = () => {
        if (!settled && !cancelled) void pollUntilDone(evaluation.id)
      }
    } catch (error) {
      callbacks.onError(error instanceof Error ? error.message : String(error))
    }
  }

  /** Read the evaluation until it completes, then rebuild the trace from evidence. */
  const pollUntilDone = async (evaluationId: string) => {
    if (polling || settled || cancelled) return
    polling = true
    for (let attempt = 0; attempt < 240 && !cancelled && !settled; attempt += 1) {
      try {
        const response = await fetch(`${API_BASE}/evaluations/${evaluationId}`)
        if (response.ok) {
          const record = (await response.json()) as {
            status: string
            verdict: string | null
            stopping_reason: string | null
            control_decisions: Record<string, ControlDecision>
          }
          if (record.status === 'completed' || record.status === 'failed') {
            if (queue.length === 0 && steps.length === 0) {
              await loadEvidence(evaluationId)
            }
            await finish(evaluationId, {
              verdict: record.verdict,
              stopping_reason: record.stopping_reason,
              control_decisions: record.control_decisions,
            })
            polling = false
            return
          }
        }
      } catch {
        // Keep polling; the engine may still be starting.
      }
      await new Promise((resolve) => window.setTimeout(resolve, 500))
    }
    polling = false
  }

  /** Rebuild the probe trace from the evidence the evaluation wrote. */
  const loadEvidence = async (evaluationId: string) => {
    try {
      const response = await fetch(`${API_BASE}/evidence?evaluation_id=${evaluationId}`)
      if (!response.ok) return
      const rows = (await response.json()) as Array<{
        suite_id: string
        control_id: string
        probe_id: string
        passed: boolean
        score: number
        payload_hash: string
        payload: Record<string, unknown>
      }>
      rows.forEach((row, index) => {
        queue.push({
          step: index + 1,
          suite_id: row.suite_id,
          control_id: row.control_id,
          probe_id: row.probe_id,
          passed: row.passed,
          score: row.score,
          locale: String(row.payload.locale ?? 'en'),
          prompt: String(row.payload.prompt ?? ''),
          response: String(row.payload.response ?? ''),
          scorer: String(row.payload.scorer ?? ''),
          evidence_type: String(row.payload.evidence_type ?? 'probe_result'),
          payload_hash: row.payload_hash,
        })
      })
      if (!draining) drain()
    } catch {
      // Leave the stream empty; the verdict is still reported.
    }
  }

  const finish = async (evaluationId: string, payload: Record<string, unknown>) => {
    if (settled) return
    settled = true
    let certificate: Certificate | null = null
    try {
      const response = await fetch(`${API_BASE}/certificates/by-evaluation/${evaluationId}`)
      if (response.ok) certificate = (await response.json()) as Certificate
    } catch {
      certificate = null
    }
    const outcome: EvaluationOutcome = {
      verdict: (payload.verdict as 'certified' | 'rejected') ?? 'rejected',
      stopping_reason: String(payload.stopping_reason ?? ''),
      control_decisions: (payload.control_decisions ?? {}) as Record<string, ControlDecision>,
      certificate,
    }
    if (queue.length > 0 || draining) {
      pending = outcome
      return
    }
    callbacks.onDone(outcome)
  }

  void run()

  return {
    cancel: () => {
      cancelled = true
      if (socket !== null) socket.close()
    },
  }
}
