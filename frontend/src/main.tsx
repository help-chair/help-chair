import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { loadRuntimeConfig } from './config/runtime'
import Root from './Root'
import './index.css'

// La configuración de tiempo de ejecución (/config.json) se lee antes de pintar,
// porque de ella depende qué sitio se muestra (público o Service Desk).
void loadRuntimeConfig().finally(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Root />
    </StrictMode>,
  )
})
