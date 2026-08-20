/**
 * The certificate.
 *
 * Printed on the light surface the design system reserves for it, since
 * gold on light fails the contrast rule and a certificate is a document
 * rather than a console. Every control is listed with the basis on which it
 * was decided and the lower bound it actually earned, which is the whole
 * point: a pass that was not statistically demonstrated says so here.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import type { Certificate } from '../lib/types'

interface CertificateViewProps {
  certificate: Certificate | null
}

function download(certificate: Certificate): void {
  const blob = new Blob([JSON.stringify(certificate, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `mizan-certificate-${certificate.id}.json`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function CertificateView({ certificate }: CertificateViewProps): React.ReactElement {
  const { t, locale } = useTranslation()
  const isArabic = locale === 'ar'

  if (certificate === null) {
    return (
      <section className="panel" data-tour="certificate">
        <h2>{t('cert.title')}</h2>
        <p className="empty">{t('cert.none')}</p>
      </section>
    )
  }

  const data = certificate.certificate_data
  const tierKey = data.evidence_tier === 'statistical' ? 'cert.tier.statistical' : 'cert.tier.budget'
  const asserts = isArabic ? data.asserts_ar : data.asserts_en
  const doesNot = isArabic ? data.does_not_assert_ar : data.does_not_assert_en

  return (
    <section className="certificate" data-theme="inverse" data-tour="certificate">
      <header className="certificate__head">
        <div>
          <p className="certificate__authority">
            {isArabic ? data.issuing_authority_ar : data.issuing_authority_en}
          </p>
          <h2 className="certificate__title">{isArabic ? data.title_ar : data.title_en}</h2>
        </div>
        <div className={`verdict-stamp verdict-stamp--${data.verdict}`}>
          {isArabic ? data.headline_ar : data.headline_en}
        </div>
      </header>

      <p className="certificate__body">{isArabic ? data.body_ar : data.body_en}</p>
      <p className={`certificate__tier certificate__tier--${data.evidence_tier}`}>{t(tierKey)}</p>

      <dl className="certificate__facts">
        <div>
          <dt>{t('cert.model')}</dt>
          <dd>
            {isArabic ? data.model.name_ar : data.model.name_en}
            <span className="mono"> {data.model.version}</span>
            <br />
            <span className="subtle">{data.model.provider}</span>
          </dd>
        </div>
        <div>
          <dt>{t('cert.usecase')}</dt>
          <dd>
            {isArabic ? data.use_case.name_ar : data.use_case.name_en}
            <br />
            <span className="subtle mono">{data.use_case.id}</span>
          </dd>
        </div>
        <div>
          <dt>{t('cert.issued')}</dt>
          <dd className="mono">{certificate.issued_at.slice(0, 19).replace('T', ' ')}</dd>
        </div>
        <div>
          <dt>{t('cert.served')}</dt>
          <dd>
            {data.evaluation_served_by.kind === 'deterministic_mock'
              ? t('submit.served.mock', { profile: data.evaluation_served_by.detail ?? '' })
              : t('submit.served.endpoint')}
          </dd>
        </div>
        <div className="certificate__facts-wide">
          <dt>{t('cert.bundle')}</dt>
          <dd className="mono hash">{certificate.evidence_bundle_hash}</dd>
        </div>
      </dl>

      <h3 className="certificate__section">{t('cert.controls')}</h3>
      <div className="table-scroll">
        <table className="table table--certificate">
          <thead>
            <tr>
              <th>{t('evidence.control')}</th>
              <th>{t('cert.control.basis')}</th>
              <th className="numeric">{t('cert.control.probes')}</th>
              <th className="numeric">{t('cert.control.required')}</th>
              <th className="numeric">{t('cert.control.bound')}</th>
            </tr>
          </thead>
          <tbody>
            {data.control_results.map((row) => (
              <tr key={row.control_id} className={row.decision === false ? 'is-failed' : undefined}>
                <td>
                  <strong>{isArabic ? row.name_ar : row.name_en}</strong>
                  <br />
                  <span className="subtle mono small">{row.framework_clause}</span>
                </td>
                <td>
                  <span
                    className={`basis basis--${row.statistically_decided ? 'primary' : 'secondary'}`}
                  >
                    {isArabic ? row.basis_labels.label_ar : row.basis_labels.label_en}
                  </span>
                </td>
                <td className="numeric mono">
                  {row.probes_passed}/{row.probes_conducted}
                </td>
                <td className="numeric mono">
                  {row.required_pass_rate === null ? '--' : row.required_pass_rate.toFixed(2)}
                </td>
                <td className="numeric mono">
                  {row.achieved_pass_rate_lower_bound === null
                    ? '--'
                    : row.achieved_pass_rate_lower_bound.toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.datasets_consulted.length === 0 ? null : (
        <>
          <h3 className="certificate__section">{t('cert.datasets')}</h3>
          <ul className="certificate__datasets">
            {data.datasets_consulted.map((dataset) => (
              <li key={dataset.dataset_id}>
                <strong>{dataset.title}</strong>
                <span className="subtle">
                  {' '}
                  {dataset.publisher} {'·'} {dataset.portal} {'·'}{' '}
                </span>
                <span className="mono">{dataset.resource_guid}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="certificate__columns">
        <div>
          <h3 className="certificate__section">{t('cert.asserts')}</h3>
          <ul className="certificate__list">
            {asserts.slice(0, 4).map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="certificate__section">{t('cert.does_not')}</h3>
          <ul className="certificate__list">
            {doesNot.slice(0, 4).map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      </div>

      <footer className="certificate__foot">
        <div>
          <p className="certificate__validity">{isArabic ? data.validity_ar : data.validity_en}</p>
          <p className="certificate__signature-note">
            {isArabic ? data.signature_note_ar : data.signature_note_en}
          </p>
          <p className="mono hash">{certificate.signature ?? ''}</p>
        </div>
        <div className="certificate__actions">
          <button
            type="button"
            className="button button--inverse"
            onClick={() => download(certificate)}
          >
            {t('cert.download')}
          </button>
          <button
            type="button"
            className="button button--inverse-quiet"
            onClick={() => window.print()}
          >
            {t('cert.print')}
          </button>
        </div>
      </footer>
    </section>
  )
}
