/**
 * Cloudflare Worker: Telegram 通知中繼站
 *
 * 用途：前端 / GitHub Actions 帶 SHARED_SECRET 打過來，Worker 驗證後
 * 從環境變數讀 TG_BOT_TOKEN + TG_CHAT_ID 代為呼叫 Telegram sendMessage。
 *
 * 安全考量：
 * - Bot Token 永遠不曝光在前端 / repo
 * - 用 SHARED_SECRET (密碼) 驗證來源
 * - CORS 預設只允許指定 origin (可在 ALLOWED_ORIGIN 設定)
 *
 * 環境變數設定 (wrangler secret put):
 *   TG_BOT_TOKEN     — Telegram bot token
 *   TG_CHAT_ID       — 目標群組 / 個人 chat id
 *   SHARED_SECRET    — 共享密碼 (前端 / Actions 用這個來認證)
 *   ALLOWED_ORIGIN   — 允許的 origin (e.g. https://你的帳號.github.io)，多個用逗號隔開；空 = 不限
 */

const MAX_TELEGRAM_LEN = 4000  // 留一點 buffer (官方上限 4096)
const TELEGRAM_API = 'https://api.telegram.org'

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(request, env) })
    }

    const url = new URL(request.url)
    if (url.pathname !== '/send') {
      return json({ error: 'not found' }, 404, request, env)
    }
    if (request.method !== 'POST') {
      return json({ error: 'method not allowed' }, 405, request, env)
    }

    let body
    try {
      body = await request.json()
    } catch {
      return json({ error: 'invalid json body' }, 400, request, env)
    }

    if (!body.password || body.password !== env.SHARED_SECRET) {
      return json({ error: 'unauthorized' }, 401, request, env)
    }
    if (!body.message || typeof body.message !== 'string') {
      return json({ error: 'message required' }, 400, request, env)
    }

    const mode = body.parse_mode || 'HTML'
    const chunks = splitMessage(body.message, MAX_TELEGRAM_LEN)
    const results = []
    for (const chunk of chunks) {
      const r = await sendTelegram(env, chunk, mode)
      results.push(r)
      if (!r.ok) break
    }
    const ok = results.every(r => r.ok)
    return json({ ok, chunks: results.length, results }, ok ? 200 : 502, request, env)
  },
}

async function sendTelegram(env, text, parse_mode) {
  if (!env.TG_BOT_TOKEN || !env.TG_CHAT_ID) {
    return { ok: false, error: 'TG_BOT_TOKEN / TG_CHAT_ID not configured' }
  }
  const r = await fetch(`${TELEGRAM_API}/bot${env.TG_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: env.TG_CHAT_ID,
      text,
      parse_mode,
      disable_web_page_preview: true,
    }),
  })
  const result = await r.json().catch(() => ({}))
  return { ok: r.ok, status: r.status, result }
}

// 訊息超過 limit 時切成多則。優先在 "\n" 處切，避免 HTML tag 斷裂。
function splitMessage(text, limit) {
  if (text.length <= limit) return [text]
  const chunks = []
  let buf = ''
  for (const line of text.split('\n')) {
    if ((buf + '\n' + line).length > limit) {
      if (buf) chunks.push(buf)
      buf = line
    } else {
      buf = buf ? buf + '\n' + line : line
    }
  }
  if (buf) chunks.push(buf)
  return chunks
}

function corsHeaders(request, env) {
  const origin = request.headers.get('Origin')
  const allowed = (env.ALLOWED_ORIGIN || '').split(',').map(s => s.trim()).filter(Boolean)
  const ok = allowed.length === 0 || (origin && allowed.includes(origin))
  return {
    'Access-Control-Allow-Origin': ok && origin ? origin : '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  }
}

function json(obj, status, request, env) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(request, env) },
  })
}
