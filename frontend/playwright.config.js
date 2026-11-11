import { defineConfig } from '@playwright/test'

// Teste de ponta a ponta: sobe a API (porta 8001) e o front (5174) contra o
// banco do DATABASE_URL do ambiente -- sempre um banco descartável, nunca o
// de produção. Como rodar: README.md ("Ponta a ponta").

const API = 'http://127.0.0.1:8001'
const FRONT = 'http://localhost:5174'

export default defineConfig({
  testDir: 'e2e',
  testMatch: '*.e2e.js',
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: { baseURL: FRONT, trace: 'retain-on-failure' },
  webServer: [
    {
      command: 'python -m uvicorn app.main:app --port 8001',
      cwd: '..',
      url: `${API}/health`,
      env: { CORS_ORIGINS: FRONT, IP_CLIENTE_CABECALHO: '' },
      reuseExistingServer: false,
    },
    {
      command: 'npx vite --port 5174 --strictPort',
      url: FRONT,
      env: { VITE_API_URL: `${API}/api/v1` },
      reuseExistingServer: false,
    },
  ],
})
