import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { initCrossOriginAuth } from './api/auth'
import './index.css'
import '@jonex/platform-theme/theme.css'
import '@jonex/platform-theme/layout.css'

initCrossOriginAuth()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
