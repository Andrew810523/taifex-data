import requests
import urllib3

# TWSE 憑證鏈缺 Subject Key Identifier，新版 OpenSSL 會驗證失敗，固關閉驗證。
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}


def _get_json(url):
    r = requests.get(url, headers=HEADERS, timeout=30, verify=False)
    r.raise_for_status()
    return r.json()


def _to_float(s):
    if s is None:
        return None
    s = str(s).replace(",", "").replace("+", "").strip()
    if s in ("", "--", "X"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def fetch_index(date_yyyymmdd: str):
    """date_yyyymmdd e.g. '20260429'. Returns dict with TAIEX close, change, change %, amount(億), high-low diff, plus actual trade date."""
    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={date_yyyymmdd}&response=json"
    j = _get_json(url)
    rows = j.get("data") or []
    if not rows:
        raise RuntimeError(f"FMTQIK 無資料: {date_yyyymmdd}")

    target = date_yyyymmdd
    target_roc = f"{int(target[:4]) - 1911}/{target[4:6]}/{target[6:8]}"

    row = next((r for r in rows if r[0].replace(" ", "") == target_roc), None)
    if row is None:
        row = rows[-1]

    trade_date_roc = row[0].replace(" ", "")
    y, m, d = trade_date_roc.split("/")
    trade_date = f"{int(y) + 1911:04d}-{int(m):02d}-{int(d):02d}"
    trade_date_compact = trade_date.replace("-", "")

    amount = _to_float(row[2])
    close = _to_float(row[4])
    change = _to_float(row[5])
    prev_close = close - change if (close is not None and change is not None) else None
    pct = (change / prev_close * 100) if prev_close else None

    high, low = _fetch_intraday_high_low(trade_date_compact)
    hl_diff = (high - low) if (high is not None and low is not None) else None

    return {
        "trade_date": trade_date,
        "加權指數": close,
        "加權指數漲跌": change,
        "加權指數當日高低差": round(hl_diff, 2) if hl_diff is not None else None,
        "加權指數漲跌幅": round(pct, 2) if pct is not None else None,
        "加權指數成交量": round(amount / 1e8, 2) if amount is not None else None,
    }


def _fetch_intraday_high_low(date_yyyymmdd: str):
    url = f"https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_INDEX?date={date_yyyymmdd}&response=json"
    try:
        j = _get_json(url)
    except Exception:
        return None, None
    rows = j.get("data") or []
    # 第一筆 09:00:00 是「前日收盤」當基準參考價，不是當日盤中真實點位，要排除。
    rows = [r for r in rows if len(r) > 1 and str(r[0]).strip() != "09:00:00"]
    vals = [_to_float(r[1]) for r in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, None
    return max(vals), min(vals)


def fetch_margin(date_yyyymmdd: str):
    url = f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={date_yyyymmdd}&selectType=ALL&response=json"
    j = _get_json(url)
    margin_amt = short_balance = None

    for table in j.get("tables", []):
        if "信用交易統計" not in table.get("title", ""):
            continue
        fields = table.get("fields", [])
        if "今日餘額" not in fields:
            continue
        idx_today = fields.index("今日餘額")
        for row in table.get("data", []):
            label = row[0] if row else ""
            if label.startswith("融資金額"):
                margin_amt = _to_float(row[idx_today])
            elif label.startswith("融券"):
                short_balance = _to_float(row[idx_today])
        break

    return {"融資金額": margin_amt, "融券": short_balance}


def fetch_dealer_spot(date_yyyymmdd: str):
    """三大法人現貨買賣超 (自營自行 / 自營避險 / 外資)。BFI82U 報表。"""
    url = f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?dayDate={date_yyyymmdd}&type=day&response=json"
    try:
        j = _get_json(url)
    except Exception:
        return {
            "自營(自行)現貨買賣超": None,
            "自營(避險)現貨買賣超": None,
            "外資現貨買賣超": None,
        }

    rows = j.get("data") or []
    fields = j.get("fields") or []

    self_buy_sell = hedge_buy_sell = foreign_buy_sell = None
    if rows and fields:
        try:
            net_idx = fields.index("買賣差額")
        except ValueError:
            net_idx = len(fields) - 1
        for row in rows:
            label = row[0] if row else ""
            if "自營商" in label and "自行" in label and self_buy_sell is None:
                self_buy_sell = _to_float(row[net_idx])
            elif "自營商" in label and "避險" in label and hedge_buy_sell is None:
                hedge_buy_sell = _to_float(row[net_idx])
            elif "外資" in label and "陸資" in label and foreign_buy_sell is None:
                foreign_buy_sell = _to_float(row[net_idx])
            elif label.strip() == "外資" and foreign_buy_sell is None:
                foreign_buy_sell = _to_float(row[net_idx])

    return {
        "自營(自行)現貨買賣超": self_buy_sell,
        "自營(避險)現貨買賣超": hedge_buy_sell,
        "外資現貨買賣超": foreign_buy_sell,
    }
