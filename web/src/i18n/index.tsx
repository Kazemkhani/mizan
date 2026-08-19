/**
 * MIZAN internationalisation (i18n) module.
 *
 * Provides a React context and hook for bilingual English/Arabic support.
 * The locale state drives both string lookup and document directionality.
 *
 * Contract for Wave 1 (RASHID):
 *   - Add or correct strings in ar.ts only; do not rename keys.
 *   - The Locale type and the useTranslation hook signature are fixed.
 *   - If a key is missing in the active catalogue, the English fallback
 *     is returned and a console warning is emitted (never a crash).
 *
 * Contract for Wave 3 (ATELIER):
 *   - Wrap your component tree with I18nProvider.
 *   - Call useTranslation() in any component to get { t, locale, setLocale, dir }.
 *   - The dir value ('ltr' | 'rtl') is updated on the <html> element automatically.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { en } from './en'
import { ar } from './ar'
import { enInterface } from './en.interface'
import { arInterface } from './ar.interface'

export type Locale = 'en' | 'ar'

// The Wave 0 shell catalogue and the interface catalogue are merged here.
// Keeping them in separate files leaves the Arabic register decisions
// recorded against the shell strings intact.
const CATALOGUES: Record<Locale, Record<string, string>> = {
  en: { ...en, ...enInterface },
  ar: { ...ar, ...arInterface },
}

/** Substitute {name} placeholders in a catalogue string. */
function interpolate(text: string, vars?: Record<string, string | number>): string {
  if (vars === undefined) return text
  return text.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in vars ? String(vars[key]) : match,
  )
}

interface I18nContextValue {
  /**
   * Translate a catalogue key. Returns the English fallback if the key is
   * absent. Placeholders of the form {name} are substituted from vars.
   */
  t: (key: string, vars?: Record<string, string | number>) => string
  /** Currently active locale. */
  locale: Locale
  /** Switch the active locale. Updates the <html> lang and dir attributes. */
  setLocale: (locale: Locale) => void
  /** Current text direction: 'ltr' for English, 'rtl' for Arabic. */
  dir: 'ltr' | 'rtl'
}

const I18nContext = createContext<I18nContextValue | null>(null)

interface I18nProviderProps {
  children: React.ReactNode
  defaultLocale?: Locale
}

export function I18nProvider({
  children,
  defaultLocale = 'en',
}: I18nProviderProps): React.ReactElement {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale)

  const dir: 'ltr' | 'rtl' = locale === 'ar' ? 'rtl' : 'ltr'

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
  }, [])

  // Synchronise the <html> element attributes whenever the locale changes.
  useEffect(() => {
    document.documentElement.lang = locale
    document.documentElement.dir = dir
  }, [locale, dir])

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>): string => {
      const catalogue = CATALOGUES[locale]
      if (key in catalogue) {
        return interpolate(catalogue[key], vars)
      }
      // Fall back to English.
      if (key in CATALOGUES.en) {
        console.warn(`[mizan/i18n] Key "${key}" missing from "${locale}" catalogue; using English fallback.`)
        return interpolate(CATALOGUES.en[key], vars)
      }
      // Key absent in all catalogues.
      console.error(`[mizan/i18n] Key "${key}" not found in any catalogue.`)
      return key
    },
    [locale],
  )

  return (
    <I18nContext.Provider value={{ t, locale, setLocale, dir }}>
      {children}
    </I18nContext.Provider>
  )
}

/** Access the active translation function and locale controls. */
export function useTranslation(): I18nContextValue {
  const ctx = useContext(I18nContext)
  if (ctx === null) {
    throw new Error('useTranslation must be called inside an I18nProvider.')
  }
  return ctx
}
