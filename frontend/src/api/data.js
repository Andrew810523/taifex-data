// 讀取 GitHub Pages 上的靜態 JSON 檔。
// 開發模式 (npm run dev): 從 ../data/ 讀本機檔
// 正式 (build): 從 同站根路徑 /data/ 讀
const BASE = import.meta.env.DEV ? '/data' : './data'

async function getJson(path) {
  const r = await fetch(`${BASE}/${path}?t=${Date.now()}`)
  if (!r.ok) throw new Error(`fetch failed: ${path} (${r.status})`)
  return r.json()
}

export const fetchLatest = () => getJson('latest.json')
export const fetchStats = () => getJson('stats.json')
export const fetchOptions = () => getJson('options.json')
export const fetchRaw = () => getJson('raw.json')
