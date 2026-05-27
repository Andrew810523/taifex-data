import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// 開發時把上一層 ../data/ 直接 serve 在 /data/ 路徑下，省去複製檔案。
function serveDataPlugin() {
  return {
    name: 'serve-data',
    configureServer(server) {
      server.middlewares.use('/data', (req, res, next) => {
        const url = req.url.split('?')[0]
        const filePath = path.join(__dirname, '..', 'data', url)
        fs.stat(filePath, (err) => {
          if (err) return next()
          res.setHeader('Content-Type', 'application/json; charset=utf-8')
          res.setHeader('Cache-Control', 'no-cache')
          fs.createReadStream(filePath).pipe(res)
        })
      })
    },
  }
}

// 部署到 GitHub Pages 時 base path 通常是 '/<repo 名>/'
// 用 VITE_BASE 環境變數覆寫，例如：VITE_BASE=/taifex-data/ npm run build
export default defineConfig({
  plugins: [react(), serveDataPlugin()],
  base: process.env.VITE_BASE || '/',
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
  },
})
