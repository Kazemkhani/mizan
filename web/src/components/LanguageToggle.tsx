/**
 * LanguageToggle component.
 *
 * Renders a button that switches between English (LTR) and Arabic (RTL).
 * Owned by ARCHITECT in Wave 0. ATELIER applies visual styling in Wave 3
 * using the design tokens from styles/tokens.css.
 */

import React from 'react'
import { useTranslation } from '../i18n'

export function LanguageToggle(): React.ReactElement {
  const { t, locale, setLocale } = useTranslation()

  const handleToggle = () => {
    setLocale(locale === 'en' ? 'ar' : 'en')
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      aria-label={t('lang.toggle.label')}
      className="lang-toggle"
      data-locale={locale}
    >
      {locale === 'en' ? 'العربية' : 'English'}
    </button>
  )
}
