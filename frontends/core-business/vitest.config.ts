import { defineConfig } from 'vitest/config';
import path from 'path';

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const pathSrc = path.resolve(__dirname, 'src');

export default defineConfig({
  root: __dirname,
  resolve: {
    alias: {
      '@': pathSrc,
      '@jonex/shell-sdk': path.resolve(__dirname, '../shared/shell-sdk/src/index.ts'),
      '@jonex/platform-theme': path.resolve(__dirname, '../shared/platform-theme/src'),
    },
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    server: {
      deps: {
        inline: ['@jonex/shell-sdk', '@jonex/platform-theme'],
      },
    },
  },
});
