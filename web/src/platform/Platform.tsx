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
import { controlRecord, fetchModels, registerModel, startEvaluation, type EvaluationOutcome, type RunHandle } from '../lib/api'
import type { DatasetBinding, Mode, ModelRow, ProbeStep, Submission, UseCase } from '../lib/types'

const STAGES = [
  { stage: 1, key: 'console.step.submit' },
  { stage: 2, key: 'console.step.usecase' },
  { stage: 3, key: 'console.step.evaluate' },
  { stage: 4, key: 'console.step.certificate' },
] as const

export type Stage = 1 | 2 | 3 | 4

interface PlatformProps {
  mode: Mode
  useCases: UseCase[]
  datasets: DatasetBinding[]
  stage: Stage
  onStage: (stage: Stage) => void
  onExit: () => void
  onStartTour: () => void
}

export function Platform({
  mode,
  useCases,
  datasets,
  stage,
  onStage,
  onExit,
  onStartTour,
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

  const useCase = useCases.find((u) => u.id === useCaseId) ?? null

  const acceptSubmission = (next: Submission, id: string | null) => {
    setSubmission(next)
    setSubmissionId(id)
    setModelId(null)
    setSteps([])
    setOutcome(null)
    setSelected(null)
    setStatus('idle')
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

  const start = () => {
    if (useCaseId === null) return
    handleRef.current?.cancel()
    setSteps([])
    setOutcome(null)
    setSelected(null)
    setErrorMessage(null)
    setStatus('running')
    handleRef.current = startEvaluation(
      mode,
      {
        modelId: modelId ?? '',
        useCaseId,
        profile: submission?.evaluation_profile ?? 'compliant',
        submissionId,
        stepDelayMs: fast ? 24 : 110,
      },
      {
        onStep: (step) => {
          setSteps((current) => [...current, step])
          if (!step.passed) setSelected(step)
        },
        onDone: (result) => {
          setOutcome(result)
          setStatus('done')
          setModels((current) =>
            current.map((m) =>
              m.id === modelId
                ? { ...m, status: result.verdict === 'certified' ? 'certified' : 'rejected' }
                : m,
            ),
          )
        },
        onError: (message) => {
          setErrorMessage(message)
          setStatus('error')
        },
      },
    )
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
    return outcome?.certificate != null
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
            />
            <EvidenceView
              step={selected}
              controlName={selected === null ? null : controlName(selected.control_id)}
              onClose={() => setSelected(null)}
            />
          </div>
        ) : null}

        {stage === 4 ? <CertificateView certificate={outcome?.certificate ?? null} /> : null}
      </main>
    </div>
  )
}
