/**
 * The introduction page.
 *
 * It answers three questions before anyone is asked to use anything: what
 * this instrument is, what you can do with it, and whose published data it
 * is grounded in. The entry control hands over to the platform with a
 * transition the App owns.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import { LanguageToggle } from '../components/LanguageToggle'
import { EntityMark } from './EntityMark'
import type { DatasetBinding, UseCase } from '../lib/types'

interface LandingProps {
  useCases: UseCase[]
  datasets: DatasetBinding[]
  controlCount: number
  onEnter: (origin: { x: number; y: number }) => void
}

export function Landing({
  useCases,
  datasets,
  controlCount,
  onEnter,
}: LandingProps): React.ReactElement {
  const { t, locale } = useTranslation()
  const isArabic = locale === 'ar'

  const enter = (event: React.MouseEvent<HTMLButtonElement>) => {
    const rect = event.currentTarget.getBoundingClientRect()
    onEnter({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 })
  }

  const entities = datasets.length
  const name = (record: { name_en: string; name_ar: string }) =>
    isArabic ? record.name_ar : record.name_en
  const description = (record: { description_en: string; description_ar: string }) =>
    isArabic ? record.description_ar : record.description_en

  return (
    <div className="landing">
      <header className="landing__bar">
        <a className="wordmark" href="#top">
          <span className="wordmark__latin">MIZAN</span>
          <span className="wordmark__arabic">ميزان</span>
        </a>
        <nav className="landing__nav" aria-label={t('landing.nav.how')}>
          <a href="#how">{t('landing.nav.how')}</a>
          <a href="#data">{t('landing.nav.data')}</a>
          <a href="#use-cases">{t('landing.nav.usecases')}</a>
          <a href="#limits">{t('landing.nav.limits')}</a>
        </nav>
        <div className="landing__bar-actions">
          <LanguageToggle />
          <button type="button" className="button button--ghost" onClick={enter}>
            {t('landing.hero.enter')}
          </button>
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero__glow" aria-hidden="true" />
          <div className="hero__content">
            <p className="eyebrow">{t('landing.hero.eyebrow')}</p>
            <h1 className="hero__title">{t('landing.hero.title')}</h1>
            <p className="hero__lede">{t('landing.hero.lede')}</p>
            <div className="hero__actions">
              <button type="button" className="button button--primary button--large" onClick={enter}>
                {t('landing.hero.enter')}
              </button>
              <a className="button button--quiet button--large" href="#how">
                {t('landing.hero.tour')}
              </a>
            </div>
            <p className="hero__caption">{t('landing.hero.caption')}</p>
          </div>

          <dl className="stat-row">
            <div className="stat">
              <dt>{t('landing.stat.controls')}</dt>
              <dd>{controlCount}</dd>
            </div>
            <div className="stat">
              <dt>{t('landing.stat.usecases')}</dt>
              <dd>{useCases.length}</dd>
            </div>
            <div className="stat">
              <dt>{t('landing.stat.entities')}</dt>
              <dd>{entities}</dd>
            </div>
            <div className="stat">
              <dt>{t('landing.stat.languages')}</dt>
              <dd className="stat__text">{t('landing.stat.languages.value')}</dd>
            </div>
          </dl>
        </section>

        <section className="section" id="how">
          <div className="section__head">
            <h2>{t('landing.what.title')}</h2>
            <p>{t('landing.what.lede')}</p>
          </div>
          <ol className="steps">
            {(['one', 'two', 'three', 'four'] as const).map((key, index) => (
              <li className="step-card" key={key}>
                <span className="step-card__number">{index + 1}</span>
                <h3>{t(`landing.step.${key}.title`)}</h3>
                <p>{t(`landing.step.${key}.body`)}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="section section--rule">
          <div className="section__head">
            <h2>{t('landing.principles.title')}</h2>
          </div>
          <div className="principles">
            {(['arabic', 'evidence', 'limits'] as const).map((key) => (
              <article className="principle" key={key}>
                <h3>{t(`landing.principle.${key}.title`)}</h3>
                <p>{t(`landing.principle.${key}.body`)}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section" id="data">
          <div className="section__head">
            <h2>{t('landing.data.title')}</h2>
            <p>{t('landing.data.lede')}</p>
          </div>
          <div className="entity-grid">
            {datasets.map((binding) => {
              const useCase = useCases.find((u) => u.id === binding.use_case_id)
              return (
                <article className="entity-card" key={binding.dataset_id}>
                  <header className="entity-card__head">
                    <EntityMark datasetId={binding.dataset_id} publisher={binding.publisher} />
                    <div>
                      <h3>{binding.publisher}</h3>
                      <p className="entity-card__portal">{binding.portal}</p>
                    </div>
                  </header>
                  <dl className="entity-card__facts">
                    <div>
                      <dt>{t('landing.data.field.dataset')}</dt>
                      <dd>{binding.title}</dd>
                    </div>
                    <div>
                      <dt>{t('landing.data.field.usecase')}</dt>
                      <dd>{useCase === undefined ? binding.use_case_id : name(useCase)}</dd>
                    </div>
                    <div>
                      <dt>{t('landing.data.field.resource')}</dt>
                      <dd className="mono truncate">{binding.resource_guid}</dd>
                    </div>
                    <div>
                      <dt>{t('landing.data.field.read')}</dt>
                      <dd className="mono">{binding.read_date}</dd>
                    </div>
                  </dl>
                  {binding.portal_url === '' ? null : (
                    <a
                      className="entity-card__link"
                      href={binding.page_url === '' ? binding.portal_url : binding.page_url}
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      {t('landing.data.open')}
                    </a>
                  )}
                </article>
              )
            })}
          </div>
          <p className="footnote">{t('landing.data.note')}</p>
        </section>

        <section className="section section--rule" id="use-cases">
          <div className="section__head">
            <h2>{t('landing.usecases.title')}</h2>
            <p>{t('landing.usecases.lede')}</p>
          </div>
          <div className="usecase-grid">
            {useCases.map((useCase) => {
              const controls = useCase.controls ?? []
              const mandatory = controls.filter((c) => c.is_mandatory).length
              return (
                <article className="usecase-card" key={useCase.id}>
                  <p className="usecase-card__id mono">{useCase.id}</p>
                  <h3>{name(useCase)}</h3>
                  <p className="usecase-card__body">{description(useCase)}</p>
                  <dl className="usecase-card__meta">
                    <div>
                      <dt>{t('landing.usecases.threshold')}</dt>
                      <dd className="mono">
                        {Math.round(useCase.confidence_threshold * 100)}%
                      </dd>
                    </div>
                    {controls.length === 0 ? null : (
                      <div>
                        <dt>{t('landing.usecases.controls')}</dt>
                        <dd className="mono">
                          {controls.length} ({mandatory} {t('landing.usecases.mandatory')})
                        </dd>
                      </div>
                    )}
                  </dl>
                </article>
              )
            })}
          </div>
        </section>

        <section className="section section--quiet" id="limits">
          <div className="limits">
            <h2>{t('landing.limits.title')}</h2>
            <p>{t('landing.limits.body')}</p>
            <button type="button" className="button button--primary button--large" onClick={enter}>
              {t('landing.hero.enter')}
            </button>
          </div>
        </section>
      </main>

      <footer className="landing__footer">
        <span className="wordmark__latin">MIZAN</span>
        <small>{t('landing.footer.note')}</small>
      </footer>
    </div>
  )
}
