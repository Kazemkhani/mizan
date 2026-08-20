/**
 * Submission panel: read a submission file, show what it says, register it.
 *
 * The upload is deliberately the primary path. A submission is a document
 * an entity hands over, and reading it back before anything is registered
 * is how the person submitting sees what they are actually attesting to.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import { SAMPLE_SUBMISSIONS } from '../data/samples'
import type { ModelRow, Submission } from '../lib/types'

const SAMPLE_FILES = [
  { id: 'agent-compliant-arabic-assistant', key: 'compliant' },
  { id: 'agent-unsafe-multilingual', key: 'non_compliant' },
  { id: 'agent-undocumented', key: 'incomplete' },
] as const

interface SubmitProps {
  submission: Submission | null
  submissionId: string | null
  registered: boolean
  models: ModelRow[]
  onSubmission: (submission: Submission, submissionId: string | null) => void
  onRegister: () => void
}

/**
 * Human labels for model card fields. Keys absent from this map are not shown.
 * Object values are expanded into labelled sub-rows. Booleans render as Yes / No.
 */
const MODEL_CARD_LABELS: Record<string, string> = {
  uae_governance_alignment:   'Alignment with UAE AI governance principles',
  processes_personal_data:    'Processes personal data',
  pdpl_compliance_notes_en:   'Notes on PDPL compliance',
  intended_use:               'Intended use',
  limitations:                'Known limitations',
  risks:                      'Known risks',
  mitigation:                 'Risk mitigation',
  training_data:              'Training data',
  evaluation_data:            'Evaluation data',
  license:                    'Licence',
  contact:                    'Contact',
}

/** Labels for nested object keys inside uae_governance_alignment. */
const GOVERNANCE_LABELS: Record<string, string> = {
  transparency:   'Transparency',
  accountability: 'Accountability',
  fairness:       'Fairness',
  safety:         'Safety',
  privacy:        'Privacy',
}

function renderModelCardValue(key: string, value: unknown): React.ReactNode {
  if (typeof value === 'boolean') {
    return <span>{value ? 'Yes' : 'No'}</span>
  }
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    const labels = key === 'uae_governance_alignment' ? GOVERNANCE_LABELS : {}
    return (
      <dl className="submission-card__sub">
        {Object.entries(value as Record<string, unknown>).map(([subKey, subVal]) => {
          const subLabel = labels[subKey] ?? subKey
          return (
            <div key={subKey}>
              <dt>{subLabel}</dt>
              <dd>{String(subVal)}</dd>
            </div>
          )
        })}
      </dl>
    )
  }
  if (Array.isArray(value)) {
    return (
      <ul className="submission-card__list">
        {value.map((item, i) => <li key={i}>{String(item)}</li>)}
      </ul>
    )
  }
  const str = String(value)
  return str === '' ? <span className="dim">(not provided)</span> : <span>{str}</span>
}

/** Validate the shape of an uploaded file, tolerating the extra sample keys. */
function parseSubmission(raw: unknown): Submission | null {
  if (typeof raw !== 'object' || raw === null) return null
  const record = raw as Record<string, unknown>
  const card = record.model_card
  if (typeof record.name_en !== 'string' || typeof card !== 'object' || card === null) {
    return null
  }
  const profile = record.evaluation_profile === 'non_compliant' ? 'non_compliant' : 'compliant'
  return {
    name_en: record.name_en,
    name_ar: typeof record.name_ar === 'string' && record.name_ar !== '' ? record.name_ar : record.name_en,
    provider: typeof record.provider === 'string' ? record.provider : 'Unstated provider',
    version: typeof record.version === 'string' ? record.version : '1.0.0',
    endpoint_url: typeof record.endpoint_url === 'string' ? record.endpoint_url : null,
    evaluation_profile: profile,
    model_card: card as Record<string, unknown>,
  }
}

export function Submit({
  submission,
  submissionId,
  registered,
  models,
  onSubmission,
  onRegister,
}: SubmitProps): React.ReactElement {
  const { t, locale } = useTranslation()
  const [dragging, setDragging] = React.useState(false)
  const [error, setError] = React.useState(false)
  const inputRef = React.useRef<HTMLInputElement>(null)

  const readFile = async (file: File) => {
    setError(false)
    try {
      const parsed = parseSubmission(JSON.parse(await file.text()))
      if (parsed === null) {
        setError(true)
        return
      }
      const id = file.name.replace('.mizan.json', '').replace('.json', '')
      const known = SAMPLE_FILES.some((s) => s.id === id)
      onSubmission(parsed, known ? id : null)
    } catch {
      setError(true)
    }
  }

  const cardFields = submission === null ? [] : Object.entries(submission.model_card)

  return (
    <div className="panel-grid">
      <section className="panel" data-tour="submit">
        <h2>{t('submit.title')}</h2>
        <p className="panel__lede">{t('submit.lede')}</p>

        <div
          className={`dropzone${dragging ? ' dropzone--active' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            const file = e.dataTransfer.files[0]
            if (file !== undefined) void readFile(file)
          }}
        >
          <p className="dropzone__title">{t('submit.drop')}</p>
          <button
            type="button"
            className="button button--quiet"
            onClick={() => inputRef.current?.click()}
          >
            {t('submit.browse')}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept="application/json,.json"
            className="visually-hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file !== undefined) void readFile(file)
            }}
          />
        </div>

        {error ? <p className="notice notice--bad">{t('submit.file.rejected')}</p> : null}

        {submission === null ? null : (
          <div className="submission-card">
            <p className="notice notice--good">{t('submit.file.accepted')}</p>
            <h3>{locale === 'ar' ? submission.name_ar : submission.name_en}</h3>
            <dl className="submission-card__facts">
              <div>
                <dt>{t('submit.field.provider')}</dt>
                <dd>{submission.provider}</dd>
              </div>
              <div>
                <dt>{t('submit.field.version')}</dt>
                <dd className="mono">{submission.version}</dd>
              </div>
              <div>
                <dt>{t('submit.field.served')}</dt>
                <dd>
                  {submission.endpoint_url === null
                    ? t('submit.served.mock', { profile: submission.evaluation_profile })
                    : t('submit.served.endpoint')}
                </dd>
              </div>
            </dl>
            {cardFields.length > 0 && (
              <details className="submission-card__card">
                <summary>{`${cardFields.length} model card fields`}</summary>
                <dl>
                  {cardFields
                    .filter(([key]) => MODEL_CARD_LABELS[key] !== undefined)
                    .map(([key, value]) => (
                      <div key={key}>
                        <dt>{MODEL_CARD_LABELS[key]}</dt>
                        <dd>{renderModelCardValue(key, value)}</dd>
                      </div>
                    ))}
                  {cardFields.filter(([key]) => MODEL_CARD_LABELS[key] === undefined).length > 0 && (
                    <div className="submission-card__unlabelled">
                      <dt className="subtle small">Additional fields</dt>
                      <dd>
                        <dl className="submission-card__sub">
                          {cardFields
                            .filter(([key]) => MODEL_CARD_LABELS[key] === undefined)
                            .map(([key, value]) => (
                              <div key={key}>
                                <dt className="mono small">{key}</dt>
                                <dd className="small">
                                  {typeof value === 'object'
                                    ? JSON.stringify(value)
                                    : String(value) === ''
                                      ? '(not provided)'
                                      : String(value)}
                                </dd>
                              </div>
                            ))}
                        </dl>
                      </dd>
                    </div>
                  )}
                </dl>
              </details>
            )}
            <button
              type="button"
              className="button button--primary"
              onClick={onRegister}
              disabled={registered}
            >
              {registered ? t('submit.registered') : t('submit.register')}
            </button>
          </div>
        )}
      </section>

      <div className="panel-stack">
        <section className="panel" data-tour="samples">
          <h2>{t('submit.samples.title')}</h2>
          <p className="panel__lede">{t('submit.samples.lede')}</p>
          <ul className="sample-list">
            {SAMPLE_FILES.map((sample) => (
              <li key={sample.id} className={submissionId === sample.id ? 'is-selected' : undefined}>
                <div>
                  <h3>{t(`submit.sample.${sample.key}.name`)}</h3>
                  <p>{t(`submit.sample.${sample.key}.detail`)}</p>
                </div>
                <div className="sample-list__actions">
                  <button
                    type="button"
                    className="button button--primary button--small"
                    onClick={() => {
                      const bundled = SAMPLE_SUBMISSIONS[sample.id]
                      if (bundled !== undefined) onSubmission(bundled, sample.id)
                    }}
                  >
                    {t('submit.sample.use')}
                  </button>
                  <a
                    className="button button--quiet button--small"
                    href={`${import.meta.env.BASE_URL}samples/${sample.id}.mizan.json`}
                    download
                  >
                    {t('submit.sample.download')}
                  </a>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel" data-tour="registry">
          <h2>{t('submit.registry.title')}</h2>
          <p className="panel__lede">{t('submit.registry.lede')}</p>
          {models.length === 0 ? (
            <p className="empty">{t('registry.empty')}</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>{t('model.name.label')}</th>
                  <th>{t('model.provider.label')}</th>
                  <th>{t('registry.model_id.label')}</th>
                </tr>
              </thead>
              <tbody>
                {models.slice(0, 8).map((model) => (
                  <tr key={model.id}>
                    <td>{locale === 'ar' ? model.name_ar : model.name_en}</td>
                    <td className="subtle">{model.provider}</td>
                    <td>
                      <span className={`pill pill--${model.status}`}>
                        {t(`registry.status.${model.status}`)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </div>
  )
}
