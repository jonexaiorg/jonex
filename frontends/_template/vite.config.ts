import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const pathSrc = path.resolve(__dirname, 'src')

export default defineConfig(() => {
  return {
    base: '{{STANDALONE_BASE}}',
    plugins: [
      react(),
      federation({
        name: '{{APP_SCOPE}}',
        filename: 'remoteEntry.js',
        exposes: {
          './Mount': './src/remote/RemoteApp.tsx',
        },
        shared: {
          react: { singleton: true, requiredVersion: '^18.2.0' },
          'react-dom': { singleton: true, requiredVersion: '^18.2.0' },
        },
      }),
    ],
    server: {
      host: '0.0.0.0',
      port: {{DEV_PORT}},
      proxy: {
        '^{{API_PREFIX}}(?!$)': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: {
        '@': `${pathSrc}`,
        '@jonex/shell-sdk': path.resolve(__dirname, '../shared/shell-sdk/src/index.ts'),
        '@jonex/platform-theme': path.resolve(__dirname, '../shared/platform-theme/src'),
      },
    },
    build: {
      target: 'esnext',
      rollupOptions: {
        output: {
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash].[ext]',
        },
      },
    },
  }
})
