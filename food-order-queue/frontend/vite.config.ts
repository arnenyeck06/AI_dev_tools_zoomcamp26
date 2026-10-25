import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Forward API calls to the FastAPI backend (default port 8010).
    proxy: {
      '/api': process.env.API_URL ?? 'http://localhost:8010',
    },
  },
})
