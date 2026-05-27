# 台股籌碼資料自動爬取

每日自動抓取 TWSE / TAIFEX 資料，計算統計指標，輸出 Excel + JSON。

## 檔案結構

```
籌碼/
├── .github/workflows/
│   └── scrape.yml          # GitHub Actions 排程 (每天 15:15 + 21:30 CST 各跑一次)
├── data/                   # 前端用 JSON 輸出 (由 export_json.py 產生)
│   ├── raw.json            # 爬蟲資料分頁全部資料
│   ├── stats.json          # 統計分頁全部資料
│   ├── options.json        # 選擇權分頁全部資料
│   └── latest.json         # 三分頁最後一筆 + 更新時間
├── scraper.py              # 主程式：抓 TWSE + TAIFEX → 寫入 xlsx
├── stats.py                # 統計分頁計算
├── option_stats.py         # 選擇權分頁計算
├── taifex.py               # TAIFEX 端點封裝
├── twse.py                 # TWSE 端點封裝
├── excel_writer.py         # Excel 寫入 (保留樣式、僅 upsert 指定日期)
├── export_json.py          # xlsx → JSON
├── trading_day.py          # 交易日判斷 + 假日清單
├── requirements.txt        # Python 依賴
└── 籌碼資料.xlsx           # 主要資料檔 (commit 進 repo)
```

## 本機使用

```bash
# 抓今天
python scraper.py

# 抓指定日期
python scraper.py 20260527

# 重新匯出 JSON (xlsx 沒變時手動跑)
python export_json.py
```

## 部署到 GitHub Actions

### 1. 註冊 GitHub 帳號

到 https://github.com 註冊 (免費)。

### 2. 建立 repo

登入後右上角 `+` → New repository：
- Repository name：例如 `taifex-data`
- **Public**（公開；GitHub Pages 與 Actions 在 free tier 對 public repo 比較大方）
- 不要勾「Add README」「Add .gitignore」「Add license」
- Create

### 3. 推上現有檔案

打開 PowerShell / cmd，到本資料夾 `c:\Users\502029\Desktop\籌碼`：

```bash
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/<你的帳號名>/<repo 名>.git
git push -u origin main
```

第一次 push 可能要登入授權 (跳出視窗或要 Personal Access Token)。

### 4. 開啟 Actions

GitHub repo 頁面 → Actions tab → 它會自動偵測 `.github/workflows/scrape.yml` → 點 `I understand my workflows, go ahead and enable them`。

之後就會：
- 每週一到週五 **15:15 CST** 與 **21:30 CST** 自動跑
- 也可在 Actions 頁面 `Run workflow` 手動觸發 (測試用)

### 5. (Module 3) GitHub Pages 發布前端

之後做完前端再加 `.github/workflows/deploy.yml` (Vite build → push to gh-pages branch)。前端用 `fetch('https://<你的帳號>.github.io/<repo>/data/latest.json')` 讀資料。

## 排程說明

| 時間 (CST) | 用途 |
|---|---|
| 15:15 | 第一輪：TAIFEX 期貨/選擇權/三大法人、加權指數已出，但**融資融券尚未公告** |
| 21:30 | 第二輪：補齊融資融券 (TWSE 信用交易 ~17:00 出)、確認所有資料完整 |

GitHub Actions cron 可能延遲 5-15 分鐘，這是正常的。

## 假日清單維護

每年初要去 `trading_day.py` 補進該年度 TWSE 公告的休市日（春節、清明、端午、中秋、雙十、補假等）。

## Telegram 通知 (Module 4)

預定後續加：成功 / 失敗時透過 Cloudflare Worker 中繼到 Telegram (Token 不外洩、避開 CORS)。
