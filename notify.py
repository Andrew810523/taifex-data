"""把 latest.json 的關鍵指標透過 Cloudflare Worker 推到 Telegram。

環境變數：
- NOTIFY_WORKER_URL   — CF Worker /send 完整 URL
- NOTIFY_SECRET       — 與 Worker SHARED_SECRET 相符的密碼

如果這兩個 env 沒設，notify 直接 skip (不報錯)，方便還沒設好 Worker 的人。
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime


def _html_escape(s):
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _fmt(v, digits=2, plus=False):
    if v is None:
        return "—"
    try:
        n = float(v)
        s = f"{n:,.{digits}f}"
        return f"+{s}" if plus and n > 0 else s
    except (TypeError, ValueError):
        return _html_escape(v)


def build_message(latest):
    s = latest.get("stats") or {}
    o = latest.get("options") or {}
    date = s.get("日期") or o.get("日期") or "—"
    change = s.get("加權指數漲跌")
    arrow = "🔴" if (change is not None and change > 0) else ("🟢" if (change is not None and change < 0) else "⚪")

    lines = [
        f"<b>📊 台股籌碼日報 · {_html_escape(date)}</b>",
        "",
        f"{arrow} <b>加權指數</b> {_fmt(s.get('加權指數'))}  "
        f"({_fmt(change, 2, plus=True)}, {_fmt(s.get('加權指數漲跌幅(%)'))}%)",
        f"📈 <b>外資現貨買賣超</b> {_fmt(s.get('外資現貨買賣超'))} 億",
        f"📈 <b>融資金額</b> {_fmt(s.get('融資金額(億)'))} 億 "
        f"(變化 {_fmt(s.get('融資金額變化量(億)'), 2, plus=True)})",
        "",
        f"<b>外資 (大小台) 期貨未平倉</b> {_fmt(s.get('外資(大小台)期貨未平倉'))}",
        f"  · 與前日 {_fmt(s.get('外資期貨未平倉與前日增減'), 2, plus=True)}",
        f"  · 與結算 {_fmt(s.get('外資期貨未平倉與結算比'), 2, plus=True)}",
        "",
        f"<b>外資 買權/賣權比</b> {_fmt(s.get('外資買權/賣權比'), 3)}",
        f"<b>散戶 買/賣權比</b> {_fmt(s.get('散戶買/賣權比'), 3)}",
        f"<b>微台散戶多空比</b> {_fmt(s.get('微台散戶多空比'))}%",
        "",
        f"<i>更新時間：{_html_escape(latest.get('updated_at', '—'))}</i>",
    ]
    return "\n".join(lines)


def send(message, parse_mode="HTML"):
    worker_url = os.environ.get("NOTIFY_WORKER_URL")
    secret = os.environ.get("NOTIFY_SECRET")
    if not worker_url or not secret:
        print("[notify] NOTIFY_WORKER_URL / NOTIFY_SECRET 未設定，skip")
        return False

    payload = json.dumps({
        "password": secret,
        "message": message,
        "parse_mode": parse_mode,
    }).encode("utf-8")
    req = urllib.request.Request(
        worker_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", errors="replace")
            print(f"[notify] {r.status} {body[:200]}")
            return r.status == 200
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[notify] HTTPError {e.code} {body[:200]}")
        return False
    except Exception as e:
        print(f"[notify] error: {e}")
        return False


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    latest_path = os.path.join(base, "data", "latest.json")
    if not os.path.exists(latest_path):
        print(f"[notify] {latest_path} 不存在，先跑 export_json.py")
        sys.exit(0)

    with open(latest_path, "r", encoding="utf-8") as f:
        latest = json.load(f)

    msg = build_message(latest)
    if "--dry-run" in sys.argv:
        print(msg)
        return
    send(msg)


if __name__ == "__main__":
    main()
