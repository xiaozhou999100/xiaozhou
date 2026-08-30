import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 后端地址：本地 FastAPI 服务（默认 8000 端口）
const BACKEND_PROXY = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: BACKEND_PROXY,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1500,
  },
})
