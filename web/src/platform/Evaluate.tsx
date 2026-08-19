/**
 * The adjudication view.
 *
 * Two columns: the probes as they arrive, and the controls as they settle.
 * The control board is the honest part. A control shows how many probes it
 * has drawn, how many passed, and whether it has been settled, so a reader
 * can see the engine retiring controls rather than grinding through a fixed
 * list.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import type { ControlDecision, ProbeStep, UseCase } from '../lib/types'
import type { EvaluationOutcome } from '../lib/api'
import { controlRecord } from '../lib/api'

export type RunStatus = 'idle' | 'running' | 'done' | 'error'

interface EvaluateProps {
  useCase: UseCase | null
  status: RunStatus
  steps: ProbeStep[]
  outcome: EvaluationOutcome | null
  errorMessage: string | null
  selectedProbeId: string | null
  fast: boolean
  onToggleSpeed: () => void
  onStart: () => void
  onSelect: (step: ProbeStep) => void
  onOpenCertificate: () => void
  onOpenRemediation: () => void
}

interface Tally {
  controlId: string
  n: number
  passed: number
  settled: boolean
  failed: boolean
}

function tallies(
  steps: ProbeStep[],
  decisions: Record<string, ControlDecision> | undefined,
): Tally[] {
  const map = new Map<string, Tally>()
  for (const step of steps) {
    const current = map.get(step.control_id) ?? {
      controlId: step.control_id,
      n: 0,
      passed: 0,
      settled: false,
      failed: false,
    }
    current.n += 1
    if (step.passed) current.passed += 1
    map.set(step.control_id, current)
  }
  if (decisions !== undefined) {
    for (const [controlId, decision] of Object.entries(decisions)) {
      const current = map.get(controlId) ?? {
        controlId,
        n: decision.n,
        passed: decision.s,
        settled: false,
        failed: false,
      }
      current.settled = decision.decided
      current.failed = decision.decision === false
      map.set(controlId, current)
    }
  }
  return [...map.values()].sort((a, b) => a.controlId.localeCompare(b.controlId))
}

export function Evaluate({
  useCase,
  status,
  steps,
  outcome,
  errorMessage,
  selectedProbeId,
  fast,
  onToggleSpeed,
  onStart,
  onSelect,
  onOpenCertificate,
  onOpenRemediation,
}: EvaluateProps): React.ReactElement {
  const { t, locale } = useTranslation()
  const streamRef = React.useRef<HTMLOListElement>(null)
  const board = tallies(steps, outcome?.control_decisions)
  const withEvidence = board.filter((c) => c.n > 0).length

  React.useEffect(() => {
    const list = streamRef.current
    if (list !== null && status === 'running') {
      list.scrollTop = list.scrollHeight
    }
  }, [steps.length, status])

  const controlName = (controlId: string): string => {
    const record = controlRecord(controlId)
    if (record === undefined) return controlId
    return locale === 'ar' ? record.name_ar : record.name_en
  }

  return (
    <section className="evaluate" data-tour="evaluate">
      <header className="evaluate__head">
        <div>
          <h2>{t('evaluate.title')}</h2>
          <p className="panel__lede">{t('evaluate.lede')}</p>
        </div>
        <div className="evaluate__controls">
          <button
            type="button"
            className="button button--quiet button--small"
            onClick={onToggleSpeed}
          >
            {t('evaluate.speed')}: {fast ? t('evaluate.speed.fast') : t('evaluate.speed.steady')}
          </button>
          <button
            type="button"
            className="button button--primary"
            onClick={onStart}
            disabled={status === 'running'}
            data-tour="start"
          >
            {status === 'idle' ? t('evaluate.start') : t('evaluate.restart')}
          </button>
        </div>
      </header>

      <div className="gauge-row">
        <div className="gauge">
          <span className="gauge__label">{t('evaluate.probes')}</span>
          <span className="gauge__value mono">{steps.length}</span>
        </div>
        <div className="gauge">
          <span className="gauge__label">{t('evaluate.controls.settled')}</span>
          <span className="gauge__value mono">
            {withEvidence} / {board.length}
          </span>
        </div>
        <div className="gauge">
          <span className="gauge__label">{t('landing.usecases.threshold')}</span>
          <span className="gauge__value mono">
            {useCase === null ? '--' : `${Math.round(useCase.confidence_threshold * 100)}%`}
          </span>
        </div>
        <div className={`gauge gauge--status gauge--${status}`}>
          <span className="gauge__label">
            {status === 'running'
              ? t('evaluate.running')
              : status === 'done'
                ? t('evaluate.complete')
                : ''}
          </span>
          {outcome === null ? null : (
            <span
              className={`pill pill--${outcome.verdict === 'certified' ? 'certified' : 'rejected'}`}
            >
              {outcome.verdict === 'certified'
                ? t('evaluate.verdict.certified')
                : t('evaluate.verdict.rejected')}
            </span>
          )}
        </div>
      </div>

      {errorMessage === null ? null : <p className="notice notice--bad">{errorMessage}</p>}

      {outcome === null ? null : (
        <div className="outcome-bar">
          <p>
            {t(`evaluate.stopped.${outcome.stopping_reason}`) ||
              outcome.stopping_reason}
          </p>
          <span className="outcome-bar__actions">
            <button
              type="button"
              className="button button--quiet button--small"
              onClick={onOpenRemediation}
            >
              {t('evaluate.view.remediation')}
            </button>
            {outcome.certificate === null ? null : (
              <button
                type="button"
                className="button button--primary button--small"
                onClick={onOpenCertificate}
              >
                {t('evaluate.view.certificate')}
              </button>
            )}
          </span>
        </div>
      )}

      <div className="evaluate__body">
        <div className="stream">
          <h3>{t('evaluate.stream.title')}</h3>
          {steps.length === 0 ? (
            <p className="empty">{t('evaluate.stream.empty')}</p>
          ) : (
            <ol className="stream__list" ref={streamRef}>
              {steps.map((step) => (
                <li key={`${step.step}-${step.probe_id}`}>
                  <button
                    type="button"
                    className={`stream__item${selectedProbeId === step.probe_id ? ' is-selected' : ''}${
                      step.passed ? '' : ' stream__item--failed'
                    }`}
                    onClick={() => onSelect(step)}
                  >
                    <span className="stream__step mono">{String(step.step).padStart(3, '0')}</span>
                    <span className="stream__suite">{step.suite_id.replace('suite-', '')}</span>
                    <span className="stream__probe mono">{step.probe_id}</span>
                    <span className={`stream__mark ${step.passed ? 'is-pass' : 'is-fail'}`}>
                      {step.passed ? t('evaluate.passed') : t('evaluate.failed')}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          )}
        </div>

        <div className="board">
          <h3>{t('evaluate.controls.title')}</h3>
          <p className="subtle small">{t('evaluate.controls.hint')}</p>
          {board.length === 0 ? (
            <p className="empty">{t('evaluate.awaiting')}</p>
          ) : (
            <ul className="board__list">
              {board.map((control) => {
                const rate = control.n === 0 ? 0 : control.passed / control.n
                const last = [...steps].reverse().find((s) => s.control_id === control.controlId)
                return (
                  <li key={control.controlId}>
                    <button
                      type="button"
                      className={`board__item${control.failed ? ' board__item--failed' : ''}${
                        control.settled ? ' board__item--settled' : ''
                      }`}
                      onClick={() => {
                        if (last !== undefined) onSelect(last)
                      }}
                    >
                      <span className="board__name">{controlName(control.controlId)}</span>
                      <span className="board__bar" aria-hidden="true">
                        <span
                          className="board__bar-fill"
                          style={{ width: `${Math.round(rate * 100)}%` }}
                        />
                      </span>
                      <span className="board__count mono">
                        {control.passed}/{control.n}
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}
