import path from 'node:path'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // En desarrollo el cliente usa rutas relativas (/api/...); Vite las reenvía al servicio local.
  // En producción lo hace el gateway/ingress según el Host.
  const proxy = (key: string, fallback: string) => ({
    target: env[key] || fallback,
    changeOrigin: true,
  })

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        '/api/public': {
          ...proxy('VITE_API_GATEWAY_URL', 'http://localhost:8000'),
          // Prism (npm run mock:gateway) sirve las rutas sin el prefijo /api/public/v1
          ...(env.VITE_GATEWAY_MOCK === 'true' && {
            rewrite: (p: string) => p.replace(/^\/api\/public\/v1/, ''),
          }),
        },
        '/api/events': proxy('VITE_API_EVENTS_URL', 'http://localhost:8001'),
        '/api/access': proxy('VITE_API_ACCESS_URL', 'http://localhost:8002'),
        '/api/requests': proxy('VITE_API_REQUESTS_URL', 'http://localhost:8003'),
        '/api/incidents': proxy('VITE_API_INCIDENTS_URL', 'http://localhost:8004'),
        '/api/problems': proxy('VITE_API_PROBLEMS_URL', 'http://localhost:8005'),
        '/api/knowledge': proxy('VITE_API_KNOWLEDGE_URL', 'http://localhost:8006'),
      },
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: false,
    },
  }
})
