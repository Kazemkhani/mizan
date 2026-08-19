/**
 * MIZAN application root component.
 *
 * Provides the i18n context and renders the top-level shell.
 * Visual structure is intentionally minimal at Wave 0; ATELIER
 * applies the full design system in Wave 3.
 *
 * The html[lang] and html[dir] attributes are managed by the
 * I18nProvider; no manual dir-setting is needed here.
 */

import React from 'react'
import { I18nProvider, useTranslation } from './i18n'
import { LanguageToggle } from './components/LanguageToggle'

function Shell(): React.ReactElement {
  const { t } = useTranslation()

  return (
    <div className="mizan-shell">
      <header className="mizan-header">
        <div className="mizan-header__brand">
          <span className="mizan-header__name">{t('app.name')}</span>
          <span className="mizan-header__tagline">{t('app.tagline')}</span>
        </div>
        <nav className="mizan-header__nav" aria-label={t('nav.registry')}>
          <a href="#registry">{t('nav.registry')}</a>
          <a href="#evaluate">{t('nav.evaluate')}</a>
          <a href="#certificates">{t('nav.certificates')}</a>
        </nav>
        <LanguageToggle />
      </header>

      <main className="mizan-main" id="main-content">
        <section id="registry" aria-labelledby="registry-heading">
          <h1 id="registry-heading">{t('registry.title')}</h1>
          <p>{t('registry.subtitle')}</p>
          <p className="mizan-placeholder">
            {/* Wave 3: ATELIER wires the live registry table here. */}
            {t('common.loading')}
          </p>
        </section>
      </main>

      <footer className="mizan-footer">
        <small>{t('app.name')} v0.1.0</small>
      </footer>
    </div>
  )
}

export default function App(): React.ReactElement {
  return (
    <I18nProvider defaultLocale="en">
      <Shell />
    </I18nProvider>
  )
}
