/**
 * MIZAN application root.
 *
 * Two views: the introduction and the platform. The transition between them
 * is a circle that expands from the control that was pressed until it covers
 * the viewport, so the platform is revealed from the point of the decision
 * rather than replacing the page abruptly. Under a reduced-motion
 * preference the circle is skipped and the views cross-fade.
 *
 * The i18n provider owns html[lang] and html[dir]; nothing here sets them.
 */

import React from 'react'
import { I18nProvider, useTranslation } from './i18n'
import { Landing } from './landing/Landing'
import { Platform, type Stage } from './platform/Platform'
import { Walkthrough, TOUR_STEPS } from './walkthrough/Walkthrough'
import { detectMode, fetchDatasets, fetchUseCases, recordedDocument } from './lib/api'
import type { DatasetBinding, Mode, UseCase } from './lib/types'
import './styles/app.css'

const TRANSITION_MS = 780

function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

function Shell(): React.ReactElement {
  const { t } = useTranslation()
  const [view, setView] = React.useState<'landing' | 'platform'>('landing')
  const [transition, setTransition] = React.useState<{ x: number; y: number } | null>(null)
  const [mode, setMode] = React.useState<Mode>('recorded')
  const [useCases, setUseCases] = React.useState<UseCase[]>(recordedDocument().use_cases)
  const [datasets, setDatasets] = React.useState<DatasetBinding[]>(recordedDocument().datasets)
  const [stage, setStage] = React.useState<Stage>(1)
  const [tourIndex, setTourIndex] = React.useState<number | null>(null)
  const [evaluationStatus, setEvaluationStatus] = React.useState<string>('idle')
  const startEvaluationRef = React.useRef<(() => void) | null>(null)
  const resetEvaluationRef = React.useRef<(() => void) | null>(null)
  const flushEvaluationRef = React.useRef<(() => void) | null>(null)

  React.useEffect(() => {
    let active = true
    void (async () => {
      const detected = await detectMode()
      if (!active) return
      setMode(detected)
      const [cases, bindings] = await Promise.all([
        fetchUseCases(detected),
        fetchDatasets(detected),
      ])
      if (!active) return
      // The recorded catalogue carries the control list per use case; the
      // API's list endpoint does not, so the two are merged rather than
      // replaced, and the interface keeps showing control counts either way.
      setUseCases(
        cases.map((useCase) => ({
          ...useCase,
          controls:
            useCase.controls ??
            recordedDocument().use_cases.find((u) => u.id === useCase.id)?.controls,
        })),
      )
      setDatasets(bindings)
    })()
    return () => {
      active = false
    }
  }, [])

  // The walkthrough drives the stage, so a step about the certificate is
  // never explained while the submission panel is on screen.
  React.useEffect(() => {
    if (tourIndex === null) return
    const step = TOUR_STEPS[tourIndex]
    if (step !== undefined) setStage(step.stage)
  }, [tourIndex])

  const enter = (origin: { x: number; y: number }) => {
    if (prefersReducedMotion()) {
      setView('platform')
      setTourIndex(0)
      return
    }
    setTransition(origin)
    window.setTimeout(() => {
      setView('platform')
      window.scrollTo({ top: 0 })
    }, TRANSITION_MS * 0.55)
    window.setTimeout(() => {
      setTransition(null)
      setTourIndex(0)
    }, TRANSITION_MS + 120)
  }

  const exit = () => {
    setView('landing')
    setTourIndex(null)
  }

  const controlCount = recordedDocument().controls.length

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t('skiplink')}
      </a>

      {view === 'landing' ? (
        <Landing
          useCases={useCases}
          datasets={datasets}
          controlCount={controlCount}
          onEnter={enter}
        />
      ) : (
        <div id="main-content">
          <Platform
            mode={mode}
            useCases={useCases}
            datasets={datasets}
            stage={stage}
            onStage={setStage}
            onExit={exit}
            onStartTour={() => setTourIndex(0)}
            onExposeStart={(fn) => { startEvaluationRef.current = fn }}
            onExposeReset={(fn) => { resetEvaluationRef.current = fn }}
            onExposeFlush={(fn) => { flushEvaluationRef.current = fn }}
            onStatusChange={setEvaluationStatus}
          />
        </div>
      )}

      {transition === null ? null : (
        <div className="curtain" aria-hidden="true">
          <span
            className="curtain__circle"
            style={{ left: transition.x, top: transition.y }}
          />
        </div>
      )}

      {tourIndex === null ? null : (
        <Walkthrough
          index={tourIndex}
          onIndex={setTourIndex}
          onClose={() => setTourIndex(null)}
          onStartEvaluation={() => startEvaluationRef.current?.()}
          onFlushEvaluation={() => flushEvaluationRef.current?.()}
          evaluationStatus={evaluationStatus}
          onDone={() => {
            // "Start using it" on the final step: return to Submit with a clean
            // slate so the reader's first action after the tour is meaningful.
            resetEvaluationRef.current?.()
            setEvaluationStatus('idle')
            setStage(1)
            setTourIndex(null)
          }}
          onRunAgain={() => {
            resetEvaluationRef.current?.()
            setEvaluationStatus('idle')
            setStage(1)
            setTourIndex(0)
          }}
        />
      )}
    </>
  )
}

export default function App(): React.ReactElement {
  return (
    <I18nProvider defaultLocale="en">
      <Shell />
    </I18nProvider>
  )
}
