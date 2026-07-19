import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const parentEnv = loadEnv('', path.resolve(__dirname, '..'), 'VITE_API_')
const apiTarget = process.env.VITE_API_TARGET || parentEnv.VITE_API_TARGET || 'http://localhost:8000'

export default defineConfig({
  base: '/',
  resolve: {
    alias: {
      '@jonex/shell-sdk': path.resolve(__dirname, '../shared/shell-sdk/src/index.ts'),
      '@jonex/platform-theme': path.resolve(__dirname, '../shared/platform-theme/src'),
    },
  },
  plugins: [
    react(),
    federation({
      name: 'shell',
      remotes: {},
      shared: {
        react: { singleton: true, requiredVersion: '^18.2.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.2.0' },
      },
    }),
  ],
  server: {
    port: 5173,
    host: true,
    proxy: {

      '/api/': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/health': {
        target: apiTarget,
        changeOrigin: true,
      },


      '/remotes/core-business/': {
        target: 'http://localhost:5175',
        changeOrigin: true,
        rewrite: (path) =>
          path.includes('remoteEntry.js')
            ? '/@id/__x00__virtual:__federation_remote_coreBusiness_entry' + (path.includes('?') ? path.substring(path.indexOf('?')) : '')
            : path.replace(/^\/remotes/, ''),
      },
      '/remotes/platform-management/': {
        target: 'http://localhost:5177',
        changeOrigin: true,
        rewrite: (path) =>
          path.includes('remoteEntry.js')
            ? '/@id/__x00__virtual:__federation_remote_platformManagement_entry' + (path.includes('?') ? path.substring(path.indexOf('?')) : '')
            : path.replace(/^\/remotes/, ''),
      },
      '/remotes/ecosystem-management/': {
        target: 'http://localhost:5176',
        changeOrigin: true,
        rewrite: (path) =>
          path.includes('remoteEntry.js')
            ? '/@id/__x00__virtual:__federation_remote_ecosystemManagement_entry' + (path.includes('?') ? path.substring(path.indexOf('?')) : '')
            : path.replace(/^\/remotes/, ''),
      },

      '/core-business/': {
        target: 'http://localhost:5175',
        changeOrigin: true,
      },
      '/platform-management/': {
        target: 'http://localhost:5177',
        changeOrigin: true,
      },
      '/ecosystem-management/': {
        target: 'http://localhost:5176',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'esnext',
  },
})
