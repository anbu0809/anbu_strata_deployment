import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    //host: '127.0.0.1',//local
    host: '0.0.0.0', server
    port: 3000,
    proxy: {
      '/api': {
        //target: 'http://127.0.0.1:8000',//local
        target: 'http://34.41.49.200:8000', server
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  appType: 'spa', // Set the app type to single page application
})