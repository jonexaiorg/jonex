import React from 'react'
import ReactDOM from 'react-dom/client'
import { I18nextProvider } from 'react-i18next'
import App from './App'
import i18n from './locales/i18n'
import { initCrossOriginAuth } from './api/auth'
import './index.css'
import '@jonex/platform-theme/theme.css'
import '@jonex/platform-theme/layout.css'

initCrossOriginAuth()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <I18nextProvider i18n={i18n}>
      <App />
    </I18nextProvider>
  </React.StrictMode>,
)
