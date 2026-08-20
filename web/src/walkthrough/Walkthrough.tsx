/**
 * The guided walkthrough.
 *
 * A spotlight over the element a step is about, and a card explaining it.
 * Steps are anchored by data-tour attributes rather than by position, so a
 * layout change cannot silently point the spotlight at the wrong thing.
 *
 * Three safety rules:
 *   1. A step whose anchor is absent is centred (original behaviour, kept).
 *   2. A step whose anchor exists but has no visible children is also centred,
 *      because spotlighting an empty placeholder is worse than absence.
 *   3. When advancing to the 'evidence' step the tour starts the evaluation
 *      itself, so the stream is populated and the instruction is live.
 */

import React from 'react'
import { useTranslation } from '../i18n'

export interface TourStep {
  /** Key prefix in the string catalogue: tour.<key>.title and .body */
  key: string
  /** data-tour value of the element to spotlight, or null to centre. */
  anchor: string | null
  /** Stage the interface should be showing for this step. */
  stage: 1 | 2 | 3 | 4 | 5
}

export const TOUR_STEPS: TourStep[] = [
  { key: 'welcome',     anchor: null,          stage: 1 },
  { key: 'submit',      anchor: 'samples',     stage: 1 },
  { key: 'registry',    anchor: 'registry',    stage: 1 },
  { key: 'usecase',     anchor: 'usecase',     stage: 2 },
  { key: 'evaluate',    anchor: 'start',       stage: 3 },
  // 'evidence': anchor changed to 'stream' (the verification log container)
  // and the tour auto-starts the evaluation when reaching this step so
  // the stream is populated rather than empty.
  { key: 'evidence',    anchor: 'stream',      stage: 3 },
  { key: 'certificate', anchor: 'certificate', stage: 4 },
  { key: 'remediation', anchor: 'remediation', stage: 5 },
]

const EVIDENCE_STEP_INDEX = TOUR_STEPS.findIndex((s) => s.key === 'evidence')

interface Rect {
  top: number
  left: number
  width: number
  height: number
}

/** True if the element is present but empty (no children, no text). */
function isVisiblyEmpty(el: Element): boolean {
  return el.childElementCount === 0 && (el.textContent ?? '').trim() === ''
}

interface WalkthroughProps {
  index: number
  onIndex: (index: number) => void
  onClose: () => void
  /** Called when the tour needs to start the evaluation (step 'evidence'). */
  onStartEvaluation?: () => void
  /**
   * Current evaluation status from Platform. Used for the button label while
   * the stream is still empty. Matches RunStatus: 'idle'|'running'|'done'|'error'.
   */
  evaluationStatus?: string
  /**
   * Called when advancing past the evidence step while the evaluation is still
   * running. Flushes the remaining animation and emits onDone immediately, so
   * the certificate is ready when the spotlight lands on the next step.
   */
  onFlushEvaluation?: () => void
  /** Called when the demonstrator presses "Run it again" on the final step. */
  onRunAgain?: () => void
  /**
   * Called when the reader finishes the tour by pressing "Start using it" on
   * the final step. Distinct from onClose (which is skip/early exit) so the
   * caller can navigate to Submit and reset state rather than leaving whatever
   * stage the tour happened to end on.
   */
  onDone?: () => void
}

const PADDING = 10

/** Position of the card relative to the spotlight. */
type CardPosition = 'below' | 'above' | 'centre'

export function Walkthrough({
  index,
  onIndex,
  onClose,
  onStartEvaluation,
  evaluationStatus,
  onFlushEvaluation,
  onRunAgain,
  onDone,
}: WalkthroughProps): React.ReactElement | null {
  const { t } = useTranslation()
  const [rect, setRect] = React.useState<Rect | null>(null)
  const [cardPos, setCardPos] = React.useState<CardPosition>('centre')
  // Tracks whether the verification stream has at least one item. Computed
  // locally by polling the DOM so no threading from Platform is needed.
  const [streamHasItems, setStreamHasItems] = React.useState(false)
  const step = TOUR_STEPS[index]

  React.useEffect(() => {
    if (step === undefined) return undefined

    // When entering the evidence step, start the evaluation so the stream
    // is populated before the spotlight is drawn.
    if (index === EVIDENCE_STEP_INDEX) {
      onStartEvaluation?.()
    }

    if (step.anchor === null) {
      setRect(null)
      setCardPos('centre')
      return undefined
    }

    const anchor = step.anchor

    // Place the spotlight over the anchor element and compute card position.
    // Re-called on scroll/resize via the listeners below.
    const measureEl = (el: Element) => {
      const box = el.getBoundingClientRect()
      if (box.top < 0 || box.bottom > window.innerHeight) {
        // Scroll the element into view and re-measure once settled.
        el.scrollIntoView({ block: 'center', behavior: 'smooth' })
        window.setTimeout(() => {
          const current = document.querySelector(`[data-tour="${anchor}"]`)
          if (current !== null && !isVisiblyEmpty(current)) measureEl(current)
        }, 400)
        return
      }
      const r: Rect = {
        top: box.top - PADDING,
        left: box.left - PADDING,
        width: box.width + PADDING * 2,
        height: box.height + PADDING * 2,
      }
      setRect(r)
      const below = r.top + r.height + 16
      setCardPos(below + 220 < window.innerHeight ? 'below' : 'above')
    }

    // Re-measure on viewport changes once the element has been found.
    const remeasure = () => {
      const el = document.querySelector(`[data-tour="${anchor}"]`)
      if (el !== null && !isVisiblyEmpty(el)) measureEl(el)
    }
    window.addEventListener('resize', remeasure)
    window.addEventListener('scroll', remeasure, true)

    // Poll until the anchor element appears and has visible content.
    //
    // Walkthrough's effects run before App's stage-setting effect (React
    // fires child effects before parent effects). This means the panel for
    // the new stage is not yet in the DOM when the effect first runs. A
    // bounded retry races the commit; polling until the condition is true
    // does not. The interval fires every 50 ms, which is faster than one
    // render cycle, so the spotlight appears within one frame of the
    // panel's commit with zero visible delay to the user.
    let pollId: number | undefined

    const tryMeasure = (): boolean => {
      const el = document.querySelector(`[data-tour="${anchor}"]`)
      if (el === null || isVisiblyEmpty(el)) return false
      if (pollId !== undefined) {
        window.clearInterval(pollId)
        pollId = undefined
      }
      measureEl(el)
      return true
    }

    if (!tryMeasure()) {
      pollId = window.setInterval(tryMeasure, 50)
    }

    return () => {
      if (pollId !== undefined) window.clearInterval(pollId)
      window.removeEventListener('resize', remeasure)
      window.removeEventListener('scroll', remeasure, true)
    }
  }, [index, step, onStartEvaluation])

  // Poll the verification stream for its first item. The gate on the Next
  // button uses streamHasItems rather than evaluationStatus === 'done', so the
  // reader can advance within seconds rather than after the full run finishes.
  React.useEffect(() => {
    if (index !== EVIDENCE_STEP_INDEX) {
      // Leaving the evidence step; reset so the second pass starts clean.
      setStreamHasItems(false)
      return
    }

    const poll = window.setInterval(() => {
      const stream = document.querySelector('[data-tour="stream"]')
      if (stream !== null && stream.childElementCount > 0) {
        setStreamHasItems(true)
        window.clearInterval(poll)
      }
    }, 150)

    return () => window.clearInterval(poll)
  }, [index])

  React.useEffect(() => {
    const waitingForEvaluation = index === EVIDENCE_STEP_INDEX && !streamHasItems
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
      if (event.key === 'ArrowRight' && !waitingForEvaluation) {
        // Flush the evaluation when advancing beyond the evidence step so
        // the certificate is ready by the time the spotlight lands.
        if (index === EVIDENCE_STEP_INDEX && evaluationStatus !== 'done') {
          onFlushEvaluation?.()
        }
        onIndex(Math.min(index + 1, TOUR_STEPS.length - 1))
      }
      if (event.key === 'ArrowLeft') onIndex(Math.max(index - 1, 0))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [index, onIndex, onClose, evaluationStatus, streamHasItems, onFlushEvaluation])

  if (step === undefined) return null

  const isLast = index === TOUR_STEPS.length - 1
  // Gate on stream having at least one item rather than evaluation being fully
  // complete. The stream has something clickable within the first second or
  // two, so the reader can advance almost immediately and watch the assessment
  // continue behind them -- a better demonstration than a stationary wait.
  const waitingForEvaluation = index === EVIDENCE_STEP_INDEX && !streamHasItems

  const cardStyle: React.CSSProperties = {}
  if (rect !== null && cardPos !== 'centre') {
    const below = rect.top + rect.height + 16
    cardStyle.top = cardPos === 'below' ? below : Math.max(16, rect.top - 236)
    cardStyle.left = Math.min(
      Math.max(16, rect.left),
      Math.max(16, window.innerWidth - 420),
    )
  }

  const isCentred = rect === null || cardPos === 'centre'

  return (
    // Click on the dimmed area closes the tour. Propagation from the card is
    // stopped below so only the background area triggers close.
    <div className="tour" role="dialog" aria-modal="true" aria-label={t('console.guide')} onClick={onClose}>
      {/* The spotlight's box-shadow provides the single dim layer. The old
          .tour__scrim was a second full-screen overlay that stacked with it,
          producing 92% effective opacity. Only the spotlight dim survives. */}
      {rect === null ? null : (
        <div
          className="tour__spotlight"
          style={{ top: rect.top, left: rect.left, width: rect.width, height: rect.height }}
        />
      )}
      <div
        className={`tour__card${isCentred ? ' tour__card--centre' : ` tour__card--${cardPos}`}`}
        style={isCentred ? undefined : cardStyle}
        // Prevent clicks on the card from bubbling up to the tour close handler.
        onClick={(e) => e.stopPropagation()}
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
            {isLast && onRunAgain !== undefined ? (
              <button
                type="button"
                className="button button--quiet button--small"
                onClick={onRunAgain}
              >
                {t('tour.run_again')}
              </button>
            ) : null}
            <button
              type="button"
              className="button button--primary button--small"
              disabled={waitingForEvaluation}
              onClick={() => {
                if (isLast) {
                  // Use onDone when it is provided (navigates to Submit with a
                  // clean state); fall back to onClose for early-exit callers.
                  ;(onDone ?? onClose)()
                  return
                }
                // Flush the evaluation when advancing beyond the evidence step
                // so the certificate is ready by the time the spotlight lands.
                if (index === EVIDENCE_STEP_INDEX && evaluationStatus !== 'done') {
                  onFlushEvaluation?.()
                }
                onIndex(index + 1)
              }}
            >
              {waitingForEvaluation && evaluationStatus === 'running'
                ? t('tour.running')
                : isLast
                  ? t('tour.done')
                  : t('tour.next')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
