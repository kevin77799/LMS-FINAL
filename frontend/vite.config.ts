import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy all /admin requests to backend
      '/admin': {
        target: 'http://127.0.0.1:8000', // use 127.0.0.1 instead of localhost
        changeOrigin: true,
        rewrite: (path) => path, // keep /admin path as-is
      },
      // Proxy /api requests to backend
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
