import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
//
// The API proxy is declared for both the dev server and the preview server.
// The websocket flag matters: the evaluation trace is streamed over
// /api/v1/ws, and without ws:true the proxy passes the HTTP request through
// but drops the upgrade, so an evaluation starts and then never reports a
// single probe.
const proxy = {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    ws: true,
  },
}

export default defineConfig({
  plugins: [react()],
  // Relative asset URLs, so a build can be served from a subdirectory such
  // as a project page on GitHub Pages as well as from a domain root.
  base: './',
  server: { port: 5173, proxy },
  preview: { port: 4173, proxy },
  build: {
    chunkSizeWarningLimit: 1600,
  },
})
