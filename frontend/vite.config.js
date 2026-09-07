import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
// En build (GitHub Pages) los assets se sirven bajo /ParidadCheck/ (nombre del repo).
// En dev se sirve desde la raíz.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/ParidadCheck/' : '/',
  plugins: [react()],
  server: {
    port: 5173,
  },
}))
