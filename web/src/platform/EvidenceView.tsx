/**
 * The exchange behind one score.
 *
 * The point of the whole instrument is that a verdict can be opened. This
 * shows the probe as it was put, the answer the model gave, the scorer that
 * judged it and the hash of the stored record, so a reader can go and check
 * it against the evidence table.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import type { ProbeStep } from '../lib/types'

interface EvidenceViewProps {
  step: ProbeStep | null
  controlName: string | null
  onClose: () => void
}

export function EvidenceView({ step, controlName, onClose }: EvidenceViewProps): React.ReactElement {
  const { t } = useTranslation()

  if (step === null) {
    return (
      <aside className="evidence evidence--empty" data-tour="evidence">
        <p className="empty">{t('evidence.empty')}</p>
      </aside>
    )
  }

  const isAttestation = step.evidence_type === 'attestation'

  return (
    <aside className="evidence" data-tour="evidence">
      <header className="evidence__head">
        <div>
          <p className="eyebrow">{t('evidence.title')}</p>
          <h3 className="mono">{step.probe_id}</h3>
        </div>
        <button type="button" className="button button--quiet button--small" onClick={onClose}>
          {t('evidence.close')}
        </button>
      </header>

      <dl className="evidence__facts">
        <div>
          <dt>{t('evidence.control')}</dt>
          <dd>
            {controlName ?? step.control_id}
            <span className="mono subtle"> {step.control_id}</span>
          </dd>
        </div>
        <div>
          <dt>{t('evidence.score')}</dt>
          <dd>
            <span className={`pill ${step.passed ? 'pill--certified' : 'pill--rejected'}`}>
              {step.passed ? t('evaluate.passed') : t('evaluate.failed')}
            </span>
            <span className="mono"> {step.score.toFixed(2)}</span>
          </dd>
        </div>
        <div>
          <dt>{t('evidence.scorer')}</dt>
          <dd className="mono">{step.scorer}</dd>
        </div>
      </dl>

      <div className="exchange">
        <p className="exchange__label">{t('evidence.prompt')}</p>
        <p className="exchange__text" dir={step.locale === 'ar' ? 'rtl' : 'ltr'}>
          {step.prompt === '' ? '(no prompt recorded)' : step.prompt}
        </p>
      </div>

      <div className="exchange">
        <p className="exchange__label">{t('evidence.response')}</p>
        {isAttestation ? (
          <p className="exchange__text subtle">{t('evidence.response.attestation')}</p>
        ) : (
          <p className="exchange__text" dir={step.locale === 'ar' ? 'rtl' : 'ltr'}>
            {step.response === '' ? '(empty response)' : step.response}
          </p>
        )}
      </div>

      <div className="evidence__hash">
        <p className="exchange__label">{t('evidence.hash')}</p>
        <p className="mono hash">{step.payload_hash}</p>
      </div>
    </aside>
  )
}
