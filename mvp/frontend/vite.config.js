import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Path to the repo-root mocks/ folder (contract-shaped fixtures from generate_mocks.py)
const MOCKS = path.resolve(__dirname, '../../../mocks')

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@mocks': MOCKS
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: true,
    proxy: {
      '/api': { 
        target: process.env.VITE_API || 'https://dung-ununited-seriately.ngrok-free.dev', 
        changeOrigin: true,
        secure: false,
        headers: {
          'ngrok-skip-browser-warning': 'true'
        }
      }
    }
  },
  preview: { host: '0.0.0.0', port: 4173, allowedHosts: true },
  build: {
    target: 'es2020',
    cssCodeSplit: true,
    reportCompressedSize: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: { 
          react: ['react', 'react-dom', 'react-router-dom'],
          vendor: ['axios']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios']
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
    include: ['tests/**/*.test.jsx'],
    env: { VITE_MOCK: '1', VITE_SHAPE: process.env.SHAPE ?? 'contract' },
    css: false
  }
})
