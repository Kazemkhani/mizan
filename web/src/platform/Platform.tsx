/**
 * The platform shell.
 *
 * Four stages, in the order the work actually happens: submit a model,
 * choose the use case, watch the adjudication, read the certificate. The
 * stage rail is the only navigation, because there is no other order in
 * which these steps make sense.
 *
 * The shell owns the evaluation state and hands it to the panels. The panels
 * do not know whether the evidence arrived from a live engine or from a
 * recorded run; that distinction is stated once, in the header.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import { LanguageToggle } from '../components/LanguageToggle'
import { Submit } from './Submit'
import { UseCasePicker } from './UseCasePicker'
import { Evaluate, type RunStatus } from './Evaluate'
import { EvidenceView } from './EvidenceView'
import { CertificateView } from './CertificateView'
import { Remediation } from './Remediation'
import { SAMPLE_SUBMISSIONS } from '../data/samples'
import { controlRecord, fetchModels, registerModel, startEvaluation, type EvaluationOutcome, type RunHandle } from '../lib/api'
import type { DatasetBinding, Mode, ModelRow, ProbeStep, Submission, UseCase } from '../lib/types'

const STAGES = [
  { stage: 1, key: 'console.step.submit' },
  { stage: 2, key: 'console.step.usecase' },
  { stage: 3, key: 'console.step.evaluate' },
  { stage: 4, key: 'console.step.certificate' },
  { stage: 5, key: 'console.step.remediate' },
] as const

export type Stage = 1 | 2 | 3 | 4 | 5

// The submission that carries the fixes a remediation plan sets out. A
// retrained model does not exist to be evaluated, so the re-evaluation runs
// this one, and the interface says so rather than implying the upload itself
// was retrained.
const REMEDIATED_REFERENCE = 'agent-compliant-arabic-assistant'

interface PlatformProps {
  mode: Mode
  useCases: UseCase[]
  datasets: DatasetBinding[]
  stage: Stage
  onStage: (stage: Stage) => void
  onExit: () => void
  onStartTour: () => void
  /** Called once after mount with a stable reference to the start function. */
  onExposeStart?: (fn: () => void) => void
  /** Called once after mount with a stable reference to the evaluation reset function. */
  onExposeReset?: (fn: () => void) => void
  /**
   * Called once after mount with a stable reference to the evaluation flush
   * function. Flush is a recorded-mode shortcut: it cancels any remaining
   * step animation and emits onDone immediately.
   */
  onExposeFlush?: (fn: () => void) => void
  /** Called whenever evaluation status changes, for external observers such as the tour. */
  onStatusChange?: (status: RunStatus) => void
}

export function Platform({
  mode,
  useCases,
  datasets,
  stage,
  onStage,
  onExit,
  onStartTour,
  onExposeStart,
  onExposeReset,
  onExposeFlush,
  onStatusChange,
}: PlatformProps): React.ReactElement {
  const { t, locale } = useTranslation()

  const [submission, setSubmission] = React.useState<Submission | null>(null)
  const [submissionId, setSubmissionId] = React.useState<string | null>(null)
  const [modelId, setModelId] = React.useState<string | null>(null)
  const [models, setModels] = React.useState<ModelRow[]>([])
  const [useCaseId, setUseCaseId] = React.useState<string | null>('uc-001')

  const [status, setStatus] = React.useState<RunStatus>('idle')
  const [steps, setSteps] = React.useState<ProbeStep[]>([])
  const [outcome, setOutcome] = React.useState<EvaluationOutcome | null>(null)
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null)
  const [selected, setSelected] = React.useState<ProbeStep | null>(null)
  const [fast, setFast] = React.useState(false)
  const [remediated, setRemediated] = React.useState(false)
  const handleRef = React.useRef<RunHandle | null>(null)

  React.useEffect(() => {
    let active = true
    void fetchModels(mode).then((rows) => {
      if (active) setModels(rows)
    })
    return () => {
      active = false
    }
  }, [mode])

  React.useEffect(() => () => handleRef.current?.cancel(), [])

  // Keep a ref to onStatusChange so callbacks inside start() do not stale-close.
  const onStatusChangeRef = React.useRef(onStatusChange)
  React.useEffect(() => { onStatusChangeRef.current = onStatusChange })

  // Keep the stable refs current and expose them to the tour.
  React.useEffect(() => {
    startRef.current = () => start()
  })
  React.useEffect(() => {
    onExposeStart?.(() => startRef.current())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    resetRef.current = () => reset()
  })
  React.useEffect(() => {
    onExposeReset?.(() => resetRef.current())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    flushRef.current = () => flush()
  })
  React.useEffect(() => {
    onExposeFlush?.(() => flushRef.current())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const useCase = useCases.find((u) => u.id === useCaseId) ?? null

  /** Wraps setStatus and notifies the external observer (e.g. the tour). */
  const notifyStatus = (next: RunStatus) => {
    setStatus(next)
    onStatusChangeRef.current?.(next)
  }

  const acceptSubmission = (next: Submission, id: string | null) => {
    setSubmission(next)
    setSubmissionId(id)
    setRemediated(false)
    setModelId(null)
    setSteps([])
    setOutcome(null)
    setSelected(null)
    notifyStatus('idle')
  }

  const register = async () => {
    if (submission === null) return
    try {
      const id = await registerModel(mode, submission)
      setModelId(id)
      setModels((current) => [
        {
          id,
          name_en: submission.name_en,
          name_ar: submission.name_ar,
          provider: submission.provider,
          version: submission.version,
          status: 'pending',
          submitted_at: new Date().toISOString(),
        },
        ...current.filter((m) => m.id !== id),
      ])
      onStage(2)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : String(error))
    }
  }

  // Stable refs so the tour can call start/reset/flush without stale closures.
  const startRef = React.useRef<() => void>(() => { /* not yet ready */ })
  const resetRef = React.useRef<() => void>(() => { /* not yet ready */ })
  const flushRef = React.useRef<() => void>(() => { /* not yet ready */ })

  const start = (override?: { modelId: string; submissionId: string | null; profile: 'compliant' | 'non_compliant' }) => {
    if (useCaseId === null) return
    handleRef.current?.cancel()
    setSteps([])
    setOutcome(null)
    setSelected(null)
    setErrorMessage(null)
    notifyStatus('running')
    handleRef.current = startEvaluation(
      mode,
      {
        modelId: override?.modelId ?? modelId ?? '',
        useCaseId,
        profile: override?.profile ?? submission?.evaluation_profile ?? 'compliant',
        submissionId: override === undefined ? submissionId : override.submissionId,
        stepDelayMs: fast ? 24 : 110,
      },
      {
        onStep: (step) => {
          setSteps((current) => [...current, step])
          if (!step.passed) setSelected(step)
        },
        onDone: (result) => {
          setOutcome(result)
          notifyStatus('done')
          setModels((current) =>
            current.map((m) =>
              m.id === (override?.modelId ?? modelId)
                ? { ...m, status: result.verdict === 'certified' ? 'certified' : 'rejected' }
                : m,
            ),
          )
        },
        onError: (message) => {
          setErrorMessage(message)
          notifyStatus('error')
        },
      },
    )
  }

  /** Clears the evaluation state without touching the submission. Used by the tour restart. */
  const reset = () => {
    handleRef.current?.cancel()
    setSteps([])
    setOutcome(null)
    setSelected(null)
    setErrorMessage(null)
    notifyStatus('idle')
  }

  /**
   * Skips remaining step animation and emits onDone immediately. Only
   * effective for recorded runs where the result is pre-loaded. Used by the
   * tour to reach the certificate/remediation views without making the reader
   * wait through the full animation.
   */
  const flush = () => {
    handleRef.current?.flush?.()
  }

  /**
   * Submit the retrained version.
   *
   * A certificate is valid for the version assessed, so a retrained model is
   * a new submission rather than an amendment. The version is bumped, the
   * name records what happened to it, and the engine adjudicates it from
   * nothing: no result from the previous run carries over.
   */
  const resubmitRemediated = () => {
    if (submission === null) return
    const reference = SAMPLE_SUBMISSIONS[REMEDIATED_REFERENCE]
    const [major] = submission.version.split('.')
    const nextVersion = `${Number.isNaN(Number(major)) ? 2 : Number(major) + 1}.0.0`
    const retrained: Submission = {
      ...submission,
      name_en: `${submission.name_en} (remediated)`,
      name_ar: `${submission.name_ar} (بعد المعالجة)`,
      version: nextVersion,
      evaluation_profile: 'compliant',
      model_card: reference?.model_card ?? submission.model_card,
    }

    setSubmission(retrained)
    setSubmissionId(REMEDIATED_REFERENCE)
    setRemediated(true)
    onStage(3)

    void (async () => {
      let id = modelId ?? ''
      try {
        id = await registerModel(mode, retrained)
      } catch {
        id = `local-${Date.now().toString(36)}`
      }
      setModelId(id)
      setModels((current) => [
        {
          id,
          name_en: retrained.name_en,
          name_ar: retrained.name_ar,
          provider: retrained.provider,
          version: retrained.version,
          status: 'in_evaluation',
          submitted_at: new Date().toISOString(),
        },
        ...current,
      ])
      start({ modelId: id, submissionId: REMEDIATED_REFERENCE, profile: 'compliant' })
    })()
  }

  const controlName = (controlId: string): string | null => {
    const record = controlRecord(controlId)
    if (record === undefined) return null
    return locale === 'ar' ? record.name_ar : record.name_en
  }

  const reachable = (target: Stage): boolean => {
    if (target === 1) return true
    if (target === 2) return submission !== null
    if (target === 3) return useCaseId !== null && submission !== null
    if (target === 4) return outcome?.certificate != null
    return outcome !== null
  }

  return (
    <div className="platform">
      <header className="platform__bar">
        <button type="button" className="wordmark wordmark--button" onClick={onExit}>
          <span className="wordmark__latin">MIZAN</span>
          <span className="wordmark__arabic">ميزان</span>
        </button>

        <ol className="stage-rail" data-tour="rail">
          {STAGES.map((entry) => (
            <li key={entry.stage}>
              <button
                type="button"
                className={`stage-rail__item${stage === entry.stage ? ' is-current' : ''}`}
                onClick={() => onStage(entry.stage as Stage)}
                disabled={!reachable(entry.stage as Stage)}
              >
                <span className="stage-rail__number mono">{entry.stage}</span>
                <span>{t(entry.key)}</span>
              </button>
            </li>
          ))}
        </ol>

        <div className="platform__bar-actions">
          <span className={`mode-badge mode-badge--${mode}`} title={t(`console.mode.${mode}.detail`)}>
            {t(`console.mode.${mode}`)}
          </span>
          <button type="button" className="button button--quiet button--small" onClick={onStartTour}>
            {t('console.guide')}
          </button>
          <LanguageToggle />
          <button type="button" className="button button--quiet button--small" onClick={onExit}>
            {t('console.back')}
          </button>
        </div>
      </header>

      {mode === 'recorded' ? (
        <p className="mode-note">{t('console.mode.recorded.detail')}</p>
      ) : null}

      <main className="platform__main">
        {stage === 1 ? (
          <Submit
            submission={submission}
            submissionId={submissionId}
            registered={modelId !== null}
            models={models}
            onSubmission={acceptSubmission}
            onRegister={() => void register()}
          />
        ) : null}

        {stage === 2 ? (
          <UseCasePicker
            useCases={useCases}
            datasets={datasets}
            selected={useCaseId}
            onSelect={setUseCaseId}
            onContinue={() => onStage(3)}
          />
        ) : null}

        {stage === 3 ? (
          <div className="evaluate-layout">
            {remediated ? <p className="rerun-note">{t('remediate.rerun.note')}</p> : null}
            <Evaluate
              useCase={useCase}
              status={status}
              steps={steps}
              outcome={outcome}
              errorMessage={errorMessage}
              selectedProbeId={selected?.probe_id ?? null}
              fast={fast}
              onToggleSpeed={() => setFast((f) => !f)}
              onStart={start}
              onSelect={setSelected}
              onOpenCertificate={() => onStage(4)}
              onOpenRemediation={() => onStage(5)}
            />
            <EvidenceView
              step={selected}
              controlName={selected === null ? null : controlName(selected.control_id)}
              onClose={() => setSelected(null)}
            />
          </div>
        ) : null}

        {stage === 4 ? <CertificateView certificate={outcome?.certificate ?? null} /> : null}

        {stage === 5 ? (
          <div className="evaluate-layout">
            <Remediation
              outcome={outcome}
              steps={steps}
              useCase={useCase}
              modelName={locale === 'ar' ? (submission?.name_ar ?? '') : (submission?.name_en ?? '')}
              fast={fast}
              onOpenProbe={setSelected}
              onResubmit={resubmitRemediated}
            />
            <EvidenceView
              step={selected}
              controlName={selected === null ? null : controlName(selected.control_id)}
              onClose={() => setSelected(null)}
            />
          </div>
        ) : null}
      </main>
    </div>
  )
}
