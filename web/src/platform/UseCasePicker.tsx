/**
 * Use-case selection.
 *
 * This is the consequential choice in the whole flow, so it gets a page of
 * its own rather than a dropdown: the card states the confidence the
 * verdict must reach, how many controls apply, and whose published data
 * grounds the evaluation.
 */

import React from 'react'
import { useTranslation } from '../i18n'
import type { DatasetBinding, UseCase } from '../lib/types'

interface UseCasePickerProps {
  useCases: UseCase[]
  datasets: DatasetBinding[]
  selected: string | null
  onSelect: (useCaseId: string) => void
  onContinue: () => void
}

export function UseCasePicker({
  useCases,
  datasets,
  selected,
  onSelect,
  onContinue,
}: UseCasePickerProps): React.ReactElement {
  const { t, locale } = useTranslation()
  const isArabic = locale === 'ar'

  return (
    <section className="panel panel--wide" data-tour="usecase">
      <h2>{t('usecase.title')}</h2>
      <p className="panel__lede">{t('usecase.lede')}</p>

      <div className="usecase-picker">
        {useCases.map((useCase) => {
          const controls = useCase.controls ?? []
          const mandatory = controls.filter((c) => c.is_mandatory).length
          const bound = datasets.filter((d) => d.use_case_id === useCase.id)
          const isSelected = selected === useCase.id
          return (
            <button
              type="button"
              key={useCase.id}
              className={`usecase-option${isSelected ? ' is-selected' : ''}`}
              onClick={() => onSelect(useCase.id)}
              aria-pressed={isSelected}
            >
              <span className="usecase-option__id mono">{useCase.id}</span>
              <span className="usecase-option__name">
                {isArabic ? useCase.name_ar : useCase.name_en}
              </span>
              <span className="usecase-option__body">
                {isArabic ? useCase.description_ar : useCase.description_en}
              </span>
              <span className="usecase-option__meta">
                <span className="mono">
                  {Math.round(useCase.confidence_threshold * 100)}%
                </span>
                <span className="subtle">{t('landing.usecases.threshold')}</span>
                {controls.length === 0 ? null : (
                  <>
                    <span className="mono">
                      {controls.length} / {mandatory}
                    </span>
                    <span className="subtle">
                      {t('landing.usecases.controls')} / {t('landing.usecases.mandatory')}
                    </span>
                  </>
                )}
              </span>
              {bound.length === 0 ? null : (
                <span className="usecase-option__data">
                  {t('usecase.datasets')}{' '}
                  <strong>{bound.map((b) => b.publisher).join(', ')}</strong>
                </span>
              )}
            </button>
          )
        })}
      </div>

      <div className="panel__actions">
        <button
          type="button"
          className="button button--primary"
          onClick={onContinue}
          disabled={selected === null}
        >
          {t('common.continue')}
        </button>
      </div>
    </section>
  )
}
