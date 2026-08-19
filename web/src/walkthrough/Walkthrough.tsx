/**
 * The guided walkthrough.
 *
 * A spotlight over the element a step is about, and a card explaining it.
 * Steps are anchored by data-tour attributes rather than by position, so a
 * layout change cannot silently point the spotlight at the wrong thing; a
 * step whose anchor is absent is centred instead of being dropped, and the
 * walkthrough moves the interface to the stage each step belongs to.
 */

import React from 'react'
import { useTranslation } from '../i18n'

export interface TourStep {
  /** Key prefix in the string catalogue: tour.<key>.title and .body */
  key: string
  /** data-tour value of the element to spotlight, or null to centre. */
  anchor: string | null
  /** Stage the interface should be showing for this step. */
  stage: 1 | 2 | 3 | 4
}

export const TOUR_STEPS: TourStep[] = [
  { key: 'welcome', anchor: null, stage: 1 },
  { key: 'submit', anchor: 'samples', stage: 1 },
  { key: 'registry', anchor: 'registry', stage: 1 },
  { key: 'usecase', anchor: 'usecase', stage: 2 },
  { key: 'evaluate', anchor: 'start', stage: 3 },
  { key: 'evidence', anchor: 'evidence', stage: 3 },
  { key: 'certificate', anchor: 'certificate', stage: 4 },
]

interface Rect {
  top: number
  left: number
  width: number
  height: number
}

interface WalkthroughProps {
  index: number
  onIndex: (index: number) => void
  onClose: () => void
}

const PADDING = 10

export function Walkthrough({ index, onIndex, onClose }: WalkthroughProps): React.ReactElement | null {
  const { t } = useTranslation()
  const [rect, setRect] = React.useState<Rect | null>(null)
  const step = TOUR_STEPS[index]

  React.useEffect(() => {
    if (step === undefined) return undefined

    const measure = () => {
      if (step.anchor === null) {
        setRect(null)
        return
      }
      const element = document.querySelector(`[data-tour="${step.anchor}"]`)
      if (element === null) {
        setRect(null)
        return
      }
      const box = element.getBoundingClientRect()
      setRect({
        top: box.top - PADDING,
        left: box.left - PADDING,
        width: box.width + PADDING * 2,
        height: box.height + PADDING * 2,
      })
      if (box.top < 0 || box.bottom > window.innerHeight) {
        element.scrollIntoView({ block: 'center', behavior: 'smooth' })
      }
    }

    // One frame later, so the stage this step belongs to has rendered.
    const frame = window.requestAnimationFrame(() => window.setTimeout(measure, 120))
    window.addEventListener('resize', measure)
    window.addEventListener('scroll', measure, true)
    return () => {
      window.cancelAnimationFrame(frame)
      window.removeEventListener('resize', measure)
      window.removeEventListener('scroll', measure, true)
    }
  }, [index, step])

  React.useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
      if (event.key === 'ArrowRight') onIndex(Math.min(index + 1, TOUR_STEPS.length - 1))
      if (event.key === 'ArrowLeft') onIndex(Math.max(index - 1, 0))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [index, onIndex, onClose])

  if (step === undefined) return null

  const isLast = index === TOUR_STEPS.length - 1
  const cardStyle: React.CSSProperties = {}
  if (rect !== null) {
    const below = rect.top + rect.height + 16
    const fitsBelow = below + 220 < window.innerHeight
    cardStyle.top = fitsBelow ? below : Math.max(16, rect.top - 236)
    cardStyle.left = Math.min(
      Math.max(16, rect.left),
      Math.max(16, window.innerWidth - 420),
    )
  }

  return (
    <div className="tour" role="dialog" aria-modal="true" aria-label={t('console.guide')}>
      <div className="tour__scrim" onClick={onClose} />
      {rect === null ? null : (
        <div
          className="tour__spotlight"
          style={{ top: rect.top, left: rect.left, width: rect.width, height: rect.height }}
        />
      )}
      <div
        className={`tour__card${rect === null ? ' tour__card--centre' : ''}`}
        style={rect === null ? undefined : cardStyle}
      >
        <p className="tour__progress mono">
          {t('tour.progress', { n: index + 1, total: TOUR_STEPS.length })}
        </p>
        <h3>{t(`tour.${step.key}.title`)}</h3>
        <p>{t(`tour.${step.key}.body`)}</p>
        <div className="tour__actions">
          <button type="button" className="button button--quiet button--small" onClick={onClose}>
            {t('tour.skip')}
          </button>
          <div className="tour__nav">
            {index === 0 ? null : (
              <button
                type="button"
                className="button button--quiet button--small"
                onClick={() => onIndex(index - 1)}
              >
                {t('tour.back')}
              </button>
            )}
            <button
              type="button"
              className="button button--primary button--small"
              onClick={() => (isLast ? onClose() : onIndex(index + 1))}
            >
              {isLast ? t('tour.done') : t('tour.next')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
