/**
 * The remediation stage.
 *
 * Four phases, in the order the work has to happen: read the gaps the
 * evaluation found, decide what would close them, run the retraining, then
 * put the retrained version back through MIZAN.
 *
 * The first phase is measurement and the interface presents it as such. The
 * second and third are projection, and every panel that shows one carries
 * the projection mark, because a plan and a rehearsal are not evidence. The
 * fourth phase does not assert an outcome at all: it hands the reader back
 * to the evaluation, which is the only thing that can issue a certificate.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import { controlRecord } from '../lib/api'
import {
  CORPUS_RATIO,
  TRAINING_STAGES,
  TRAINING_WEIGHT,
  findGaps,
  planFixes,
  type Gap,
} from '../lib/remediation'
import type { EvaluationOutcome } from '../lib/api'
import type { ProbeStep, UseCase } from '../lib/types'

type Phase = 'gaps' | 'plan' | 'training' | 'ready'

interface RemediationProps {
  outcome: EvaluationOutcome | null
  steps: ProbeStep[]
  useCase: UseCase | null
  modelName: string
  fast: boolean
  onOpenProbe: (step: ProbeStep) => void
  onResubmit: () => void
}

const PHASES: Phase[] = ['gaps', 'plan', 'training', 'ready']

export function Remediation({
  outcome,
  steps,
  useCase,
  modelName,
  fast,
  onOpenProbe,
  onResubmit,
}: RemediationProps): React.ReactElement {
  const { t, locale } = useTranslation()
  const isArabic = locale === 'ar'

  const [phase, setPhase] = React.useState<Phase>('gaps')
  const [stageIndex, setStageIndex] = React.useState(-1)
  const [logLines, setLogLines] = React.useState<string[]>([])
  const timers = React.useRef<number[]>([])

  const gaps = React.useMemo(
    () => (outcome === null ? [] : findGaps(outcome.control_decisions, steps)),
    [outcome, steps],
  )
  const fixes = React.useMemo(() => planFixes(gaps), [gaps])

  React.useEffect(
    () => () => {
      timers.current.forEach((id) => window.clearTimeout(id))
    },
    [],
  )

  if (outcome === null) {
    return (
      <section className="panel" data-tour="remediation">
        <h2>{t('remediate.title')}</h2>
        <p className="empty">{t('remediate.none')}</p>
      </section>
    )
  }

  const controlName = (controlId: string): string => {
    const record = controlRecord(controlId)
    if (record === undefined) return controlId
    return isArabic ? record.name_ar : record.name_en
  }

  const domainName = (controlId: string): string => {
    const record = controlRecord(controlId)
    if (record === undefined) return ''
    return isArabic ? record.domain_label_ar : record.domain_label_en
  }

  const suiteKey = (suiteId: string): string => suiteId.replace('suite-', '').replace('-', '_')

  const startTraining = () => {
    setPhase('training')
    setStageIndex(0)
    setLogLines([])
    timers.current.forEach((id) => window.clearTimeout(id))
    timers.current = []

    const unit = fast ? 260 : 900
    let elapsed = 0
    TRAINING_STAGES.forEach((stage, index) => {
      elapsed += stage.weight * unit
      const id = window.setTimeout(() => {
        setLogLines((current) => [...current, t(`retrain.stage.${stage.key}.done`)])
        if (index === TRAINING_STAGES.length - 1) {
          setStageIndex(TRAINING_STAGES.length)
          setPhase('ready')
        } else {
          setStageIndex(index + 1)
        }
      }, elapsed)
      timers.current.push(id)
    })
  }

  const goTo = (next: Phase) => {
    if (next === 'training') {
      startTraining()
      return
    }
    setPhase(next)
  }

  const completedWeight = TRAINING_STAGES.slice(0, Math.max(0, stageIndex)).reduce(
    (sum, s) => sum + s.weight,
    0,
  )
  const trainingPercent = Math.round((completedWeight / TRAINING_WEIGHT) * 100)

  const mandatoryGaps = gaps.filter((g) => g.isMandatory)
  const failing = gaps.filter((g) => g.kind === 'failing' || g.kind === 'intermittent')
  const unproven = gaps.filter((g) => g.kind === 'unproven' || g.kind === 'untested')
  const corpusTotal = fixes.reduce((sum, f) => sum + f.corpusItems, 0)

  return (
    <section className="remediate" data-tour="remediation">
      <header className="remediate__head">
        <div>
          <p className="eyebrow">{t('remediate.eyebrow')}</p>
          <h2>{t('remediate.title')}</h2>
          <p className="panel__lede">{t('remediate.lede')}</p>
        </div>
        <ol className="phase-rail">
          {PHASES.map((entry, index) => (
            <li key={entry}>
              <button
                type="button"
                className={`phase-rail__item${phase === entry ? ' is-current' : ''}`}
                onClick={() => goTo(entry)}
                disabled={entry === 'ready' && phase !== 'ready'}
              >
                <span className="mono">{index + 1}</span>
                <span>{t(`remediate.phase.${entry}`)}</span>
              </button>
            </li>
          ))}
        </ol>
      </header>

      {phase === 'gaps' ? (
        <div className="remediate__body">
          <div className="gauge-row">
            <div className="gauge">
              <span className="gauge__label">{t('remediate.gaps.total')}</span>
              <span className="gauge__value mono">{gaps.length}</span>
            </div>
            <div className="gauge">
              <span className="gauge__label">{t('remediate.gaps.failing')}</span>
              <span className="gauge__value mono">{failing.length}</span>
            </div>
            <div className="gauge">
              <span className="gauge__label">{t('remediate.gaps.unproven')}</span>
              <span className="gauge__value mono">{unproven.length}</span>
            </div>
            <div className="gauge">
              <span className="gauge__label">{t('remediate.gaps.mandatory')}</span>
              <span className="gauge__value mono">{mandatoryGaps.length}</span>
            </div>
          </div>

          <p className="measured-mark">{t('remediate.gaps.measured')}</p>

          <ul className="gap-list">
            {gaps.map((gap) => (
              <li key={gap.controlId} className={`gap gap--${gap.severity}`}>
                <div className="gap__head">
                  <div>
                    <h3>{controlName(gap.controlId)}</h3>
                    <p className="subtle small">
                      {domainName(gap.controlId)}
                      <span className="mono"> {gap.controlId}</span>
                    </p>
                  </div>
                  <span className={`chip chip--${gap.severity}`}>
                    {t(`remediate.kind.${gap.kind}`)}
                  </span>
                </div>
                <dl className="gap__facts">
                  <div>
                    <dt>{t('cert.control.probes')}</dt>
                    <dd className="mono">
                      {gap.passed}/{gap.probes}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('cert.control.required')}</dt>
                    <dd className="mono">{gap.requiredPassRate.toFixed(2)}</dd>
                  </div>
                  <div>
                    <dt>{t('cert.control.bound')}</dt>
                    <dd className="mono">
                      {gap.achievedBound === null ? '--' : gap.achievedBound.toFixed(3)}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('remediate.gap.needs')}</dt>
                    <dd className="mono">{gap.probesNeeded}</dd>
                  </div>
                </dl>
                <p className="gap__reading">{t(`remediate.reading.${gap.kind}`)}</p>
                {gap.example === null ? null : (
                  <button
                    type="button"
                    className="button button--quiet button--small"
                    onClick={() => onOpenProbe(gap.example as ProbeStep)}
                  >
                    {t('remediate.gap.open')}
                  </button>
                )}
              </li>
            ))}
          </ul>

          <div className="panel__actions">
            <button type="button" className="button button--primary" onClick={() => goTo('plan')}>
              {t('remediate.gaps.next')}
            </button>
          </div>
        </div>
      ) : null}

      {phase === 'plan' ? (
        <div className="remediate__body">
          <p className="projection-mark">{t('remediate.projection')}</p>
          <p className="panel__lede">
            {t('remediate.plan.lede', {
              ratio: CORPUS_RATIO,
              items: corpusTotal.toLocaleString(locale === 'ar' ? 'ar-AE' : 'en-GB'),
            })}
          </p>

          <ul className="fix-list">
            {fixes.map((fix, index) => (
              <li key={fix.id} className="fix">
                <div className="fix__head">
                  <span className="fix__order mono">{String(index + 1).padStart(2, '0')}</span>
                  <div>
                    <h3>{t(`fix.${suiteKey(fix.suiteId)}.action`)}</h3>
                    <p className="subtle small">{t(`fix.${suiteKey(fix.suiteId)}.method`)}</p>
                  </div>
                  <span className={`chip chip--${fix.severity}`}>
                    {t(`remediate.severity.${fix.severity}`)}
                  </span>
                </div>
                <dl className="fix__facts">
                  <div>
                    <dt>{t('remediate.fix.controls')}</dt>
                    <dd>{fix.controlIds.map((id) => controlName(id)).join(', ')}</dd>
                  </div>
                  <div>
                    <dt>{t('remediate.fix.probes')}</dt>
                    <dd className="mono">
                      {fix.probesRequired.toLocaleString(locale === 'ar' ? 'ar-AE' : 'en-GB')}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('remediate.fix.corpus')}</dt>
                    <dd className="mono">
                      {fix.corpusItems.toLocaleString(locale === 'ar' ? 'ar-AE' : 'en-GB')}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('remediate.fix.target')}</dt>
                    <dd className="mono">{fix.targetPassRate.toFixed(2)}</dd>
                  </div>
                </dl>
                {useCase === null ? null : (
                  <p className="fix__source">
                    {t('remediate.fix.source', {
                      useCase: isArabic ? useCase.name_ar : useCase.name_en,
                    })}
                  </p>
                )}
              </li>
            ))}
          </ul>

          <div className="panel__actions">
            <button type="button" className="button button--quiet" onClick={() => goTo('gaps')}>
              {t('tour.back')}
            </button>
            <button type="button" className="button button--primary" onClick={startTraining}>
              {t('remediate.plan.next')}
            </button>
          </div>
        </div>
      ) : null}

      {phase === 'training' || phase === 'ready' ? (
        <div className="remediate__body">
          <p className="projection-mark">{t('remediate.simulated')}</p>

          <div className="retrain">
            <div className="retrain__progress">
              <div className="retrain__bar" aria-hidden="true">
                <span className="retrain__bar-fill" style={{ inlineSize: `${trainingPercent}%` }} />
              </div>
              <p className="retrain__caption mono">
                {t('retrain.progress', {
                  n: Math.min(stageIndex + 1, TRAINING_STAGES.length),
                  total: TRAINING_STAGES.length,
                  percent: trainingPercent,
                })}
              </p>
            </div>

            <ol className="retrain__stages">
              {TRAINING_STAGES.map((stage, index) => {
                const state =
                  index < stageIndex ? 'done' : index === stageIndex ? 'active' : 'waiting'
                return (
                  <li key={stage.key} className={`retrain__stage is-${state}`}>
                    <span className="retrain__dot" aria-hidden="true" />
                    <div>
                      <h3>{t(`retrain.stage.${stage.key}.title`)}</h3>
                      <p>
                        {t(`retrain.stage.${stage.key}.body`, {
                          items: corpusTotal.toLocaleString(locale === 'ar' ? 'ar-AE' : 'en-GB'),
                          fixes: fixes.length,
                          model: modelName,
                        })}
                      </p>
                    </div>
                  </li>
                )
              })}
            </ol>

            {logLines.length === 0 ? null : (
              <ul className="retrain__log">
                {logLines.map((line) => (
                  <li key={line} className="mono">
                    {line}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {phase === 'ready' ? (
            <>
              <div className="uplift">
                <h3>{t('remediate.uplift.title')}</h3>
                <p className="subtle small">{t('remediate.uplift.lede')}</p>
                <ul className="uplift__list">
                  {gaps.slice(0, 8).map((gap: Gap) => {
                    const before = gap.probes === 0 ? 0 : gap.passed / gap.probes
                    const after = gap.requiredPassRate
                    return (
                      <li key={gap.controlId}>
                        <span className="uplift__name">{controlName(gap.controlId)}</span>
                        <span className="uplift__track" aria-hidden="true">
                          <span
                            className="uplift__before"
                            style={{ inlineSize: `${Math.round(before * 100)}%` }}
                          />
                          <span
                            className="uplift__after"
                            style={{ inlineSize: `${Math.round(after * 100)}%` }}
                          />
                        </span>
                        <span className="uplift__values mono">
                          {before.toFixed(2)} {'>'} {after.toFixed(2)}
                        </span>
                      </li>
                    )
                  })}
                </ul>
              </div>

              <div className="handback">
                <h3>{t('remediate.handback.title')}</h3>
                <p>{t('remediate.handback.body')}</p>
                <div className="panel__actions">
                  <button type="button" className="button button--primary" onClick={onResubmit}>
                    {t('remediate.handback.action')}
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
