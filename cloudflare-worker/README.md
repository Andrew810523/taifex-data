# Cloudflare Worker — Telegram 通知中繼站

把 Bot Token 藏在 Cloudflare 環境變數裡，前端 / GitHub Actions 透過共享密碼呼叫，不會把 token 曝光也不會踩 CORS。

## 部署步驟

### 1. 申請 Telegram Bot

1. Telegram 找 `@BotFather` → `/newbot` → 拿到 **Bot Token** (像 `123456:ABC-xyz`)
2. 把機器人拉進你要收通知的群組 (或私聊它一句話)
3. 瀏覽器打開 `https://api.telegram.org/bot<TOKEN>/getUpdates` → 找到 `"chat":{"id": ...}` 拿到 **Chat ID** (群組通常是負數)

### 2. 註冊 Cloudflare 帳號

到 https://dash.cloudflare.com 免費註冊。

### 3. 安裝 Wrangler

```bash
cd cloudflare-worker
npm install
npx wrangler login    # 開瀏覽器授權
```

### 4. 設定機密

```bash
npx wrangler secret put TG_BOT_TOKEN     # 貼上 Bot Token
npx wrangler secret put TG_CHAT_ID       # 貼上 Chat ID
npx wrangler secret put SHARED_SECRET    # 自訂一組密碼 (前端 / Actions 之後要用)
```

### 5. 部署

```bash
npx wrangler deploy
```

部署成功後會給一個 URL，例如：`https://taifex-notify.<你的子網域>.workers.dev`

### 6. 測試

```bash
curl -X POST https://taifex-notify.xxx.workers.dev/send \
  -H "Content-Type: application/json" \
  -d '{"password":"你的SHARED_SECRET","message":"<b>測試通知</b>"}'
```

回 `{"ok": true, ...}` 且 Telegram 收到「**測試通知**」即成功。

## API

`POST /send`

請求 body (JSON)：
```json
{
  "password": "SHARED_SECRET",
  "message": "要送的內容",
  "parse_mode": "HTML"
}
```

- `parse_mode` 預設 `HTML`（**強烈建議**用 HTML，避免 MarkdownV2 那堆要 escape 的特殊字元 `_*[]()~>#+=|{}.!`）
- 訊息 > 4000 字會自動切成多則連續發送

回應 (JSON)：
```json
{ "ok": true, "chunks": 1, "results": [{"ok": true, "status": 200, ...}] }
```

## 安全層級

- Bot Token 不曝光：只在 Worker 環境變數
- 密碼驗證：每個請求要帶 `SHARED_SECRET`
- CORS 限制：`wrangler.toml` 的 `ALLOWED_ORIGIN` 可指定只允許特定 origin (例如 `https://你.github.io`)；若留空就靠密碼把關

## 已知坑與防禦

| 坑 | 解法 |
|---|---|
| MarkdownV1/V2 對 `-_*[]()` 等字元嚴格 | 預設 `parse_mode=HTML`，只要 escape `< > &` 三個字 |
| 單則 4096 字限制 | Worker 內 `splitMessage()` 自動切成多則 |
| CORS 預檢 | Worker 處理 `OPTIONS`，回 `Access-Control-*` headers |
| Token 外洩 | 永遠不上 repo、用 `wrangler secret` 設定 |
