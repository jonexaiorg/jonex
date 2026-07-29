import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pathSrc = path.resolve(__dirname, 'src');

const parentEnv = loadEnv('', path.resolve(__dirname, '..'), 'VITE_API_');
const apiTarget = process.env.VITE_API_TARGET || parentEnv.VITE_API_TARGET || 'http://localhost:8000';

export default defineConfig(() => {
  return {
    base: '/ecosystem-management/',
    plugins: [
      react(),
      federation({
        name: 'ecosystemManagement',
        filename: 'remoteEntry.js',
        exposes: {
          './Mount': './src/remote/RemoteApp.tsx',
        },
        shared: {
          react: { singleton: true, requiredVersion: '^18.2.0' },
          'react-dom': { singleton: true, requiredVersion: '^18.2.0' },
          // antd 系列必须 singleton 共享（详见 shell/vite.config.js 说明）：
          // 避免 shell 与 remote 各带一份 antd/cssinjs、跨实例误删 head 样式，
          // 导致 popup z-index 变量丢失、弹层被盖住。
          antd: { singleton: true, requiredVersion: '^6.4.3' },
          '@ant-design/icons': { singleton: true, requiredVersion: '^6.2.3' },
        },
      }),
    ],
    server: {
      host: '0.0.0.0',
      port: 5176,
      proxy: {
        '/api/': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: '0.0.0.0',
      port: 5176,
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
  };
});
