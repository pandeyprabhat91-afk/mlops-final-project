import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy /api → backend:8000 so dev server works without nginx
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        // Strip /api prefix — matches nginx: location /api/ { proxy_pass http://backend:8000/; }
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/demo': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
    // Enable polling for file watching inside Docker on Windows
    watch: {
      usePolling: true,
      interval: 1000,
    },
  },
})
