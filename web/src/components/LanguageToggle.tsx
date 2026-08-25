/**
 * LanguageToggle component.
 *
 * Renders a button that switches between English (LTR) and Arabic (RTL).
 * Direction is owned by the i18n provider and styling uses the shared tokens.
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
