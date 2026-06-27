/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    exclude: ['e2e/**', 'node_modules/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/**/*.test.*',
        'src/**/*.spec.*',
        'src/main.tsx',
        'src/App.css',
        'src/index.css',
        'src/assets/**',
        'src/components/ui/avatar.tsx',
        'src/components/ui/badge.tsx',
        'src/components/ui/button.tsx',
        'src/components/ui/command.tsx',
        'src/components/ui/dialog.tsx',
        'src/components/ui/dropdown-menu.tsx',
        'src/components/ui/input.tsx',
        'src/components/ui/input-group.tsx',
        'src/components/ui/scroll-area.tsx',
        'src/components/ui/separator.tsx',
        'src/components/ui/tabs.tsx',
        'src/components/ui/textarea.tsx',
        'src/components/ui/tooltip.tsx',
      ],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
})
