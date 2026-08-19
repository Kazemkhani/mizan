/**
 * MIZAN web application entry point.
 *
 * Import order:
 *   1. ATELIER design tokens (custom properties; no side effects).
 *   2. ATELIER base styles (typography reset, document defaults).
 *   3. React and the application root.
 *
 * ATELIER owns styles/tokens.css and styles/base.css. Do not add
 * competing styles to either file.
 */

import './styles/tokens.css'
import './styles/base.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

const root = document.getElementById('root')
if (root === null) {
  throw new Error('Root element #root not found in the document.')
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
