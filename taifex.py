import io
import requests
import urllib3
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

FUT_URL = "https://www.taifex.com.tw/cht/3/futContractsDateDown"
OPT_URL = "https://www.taifex.com.tw/cht/3/callsAndPutsDateDown"
TX_DAILY_URL = "https://www.taifex.com.tw/cht/3/futDataDown"
PCR_URL = "https://www.taifex.com.tw/cht/3/pcRatioDown"

PRODUCT_NAMES = {
    "TX": ["臺股期貨", "台股期貨"],
    "MTX": ["小型臺指期貨", "小型台指期貨"],
    "TMF": ["微型臺指期貨", "微型台指期貨"],
}


def _post_csv(url, date_slash):
    data = {
        "queryStartDate": date_slash,
        "queryEndDate": date_slash,
        "commodityId": "",
    }
    r = requests.post(url, data=data, headers=HEADERS, timeout=30, verify=False)
    r.raise_for_status()
    text = r.content.decode("ms950", errors="replace")
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip() for c in df.columns]
    return df


def _matches_product(name, key):
    name = str(name).strip()
    return any(p in name for p in PRODUCT_NAMES[key])


def _to_int(v):
    if pd.isna(v):
        return 0
    try:
        return int(str(v).replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0


def _to_float(v):
    if pd.isna(v):
        return None
    s = str(v).replace(",", "").strip()
    if s in ("", "-", "--"):
        return None
    try:
        return float(s)
    except (ValueError, AttributeError):
        return None


def fetch_futures(date_yyyymmdd: str):
    """三大法人區分各期貨契約 — TX/MTX/TMF 多空未平倉口數。"""
    y, m, d = date_yyyymmdd[:4], date_yyyymmdd[4:6], date_yyyymmdd[6:8]
    df = _post_csv(FUT_URL, f"{y}/{m}/{d}")

    name_col = next((c for c in df.columns if "商品名稱" in c), None)
    role_col = next((c for c in df.columns if "身份別" in c or "身分別" in c), None)
    long_oi_col = next((c for c in df.columns if "多方未平倉口數" in c), None)
    short_oi_col = next((c for c in df.columns if "空方未平倉口數" in c), None)

    if not all([name_col, role_col, long_oi_col, short_oi_col]):
        raise RuntimeError(f"TAIFEX 期貨 CSV 欄位缺漏: {list(df.columns)}")

    out = {}
    for key in ["TX", "MTX", "TMF"]:
        sub = df[df[name_col].apply(lambda v: _matches_product(v, key))]
        foreign_long = sub[sub[role_col].str.contains("外資", na=False)][long_oi_col].apply(_to_int).sum()
        foreign_short = sub[sub[role_col].str.contains("外資", na=False)][short_oi_col].apply(_to_int).sum()
        dealer_long = sub[sub[role_col].str.contains("自營", na=False)][long_oi_col].apply(_to_int).sum()
        dealer_short = sub[sub[role_col].str.contains("自營", na=False)][short_oi_col].apply(_to_int).sum()
        total_long = sub[long_oi_col].apply(_to_int).sum()
        total_short = sub[short_oi_col].apply(_to_int).sum()
        out[key] = {
            "外資多": foreign_long, "外資空": foreign_short,
            "自營多": dealer_long, "自營空": dealer_short,
            "三大法人多": total_long, "三大法人空": total_short,
        }

    return {
        "外資大台期貨未平倉": out["TX"]["外資多"] - out["TX"]["外資空"],
        "外資小台期貨未平倉": out["MTX"]["外資多"] - out["MTX"]["外資空"],
        "外資微台期貨未平倉": out["TMF"]["外資多"] - out["TMF"]["外資空"],
        "自營大台期貨未平倉": out["TX"]["自營多"] - out["TX"]["自營空"],
        "自營小台期貨未平倉": out["MTX"]["自營多"] - out["MTX"]["自營空"],
        "自營微台期貨未平倉": out["TMF"]["自營多"] - out["TMF"]["自營空"],
        "三大法人多方小台口數": out["MTX"]["三大法人多"],
        "三大法人空方小台口數": out["MTX"]["三大法人空"],
        "三大法人多方微台口數": out["TMF"]["三大法人多"],
        "三大法人空方微台口數": out["TMF"]["三大法人空"],
    }


def fetch_options(date_yyyymmdd: str):
    """三大法人選擇權買賣權分計 — TXO 外資/自營 BC/SC/BP/SP 與 OP 未平倉。"""
    y, m, d = date_yyyymmdd[:4], date_yyyymmdd[4:6], date_yyyymmdd[6:8]
    df = _post_csv(OPT_URL, f"{y}/{m}/{d}")

    name_col = next((c for c in df.columns if "商品名稱" in c), None)
    cp_col = next((c for c in df.columns if "買賣權" in c), None)
    role_col = next((c for c in df.columns if "身份別" in c or "身分別" in c), None)
    long_lot_col = next((c for c in df.columns if "買方交易口數" in c), None)
    long_amt_col = next((c for c in df.columns if "買方交易契約金額" in c), None)
    short_lot_col = next((c for c in df.columns if "賣方交易口數" in c), None)
    short_amt_col = next((c for c in df.columns if "賣方交易契約金額" in c), None)
    long_oi_lot_col = next((c for c in df.columns if "買方未平倉口數" in c), None)
    long_oi_amt_col = next((c for c in df.columns if "買方未平倉契約金額" in c), None)
    short_oi_lot_col = next((c for c in df.columns if "賣方未平倉口數" in c), None)
    short_oi_amt_col = next((c for c in df.columns if "賣方未平倉契約金額" in c), None)

    required = [name_col, cp_col, role_col, long_lot_col, short_lot_col,
                long_amt_col, short_amt_col, long_oi_lot_col, long_oi_amt_col,
                short_oi_lot_col, short_oi_amt_col]
    if not all(required):
        raise RuntimeError(f"TAIFEX 選擇權 CSV 欄位缺漏: {list(df.columns)}")

    df = df[df[name_col].astype(str).str.contains("臺指選擇權|台指選擇權", na=False)]

    def pick(role_kw, cp_kw):
        sub = df[df[role_col].astype(str).str.contains(role_kw, na=False)
                 & df[cp_col].astype(str).str.upper().str.contains(cp_kw, na=False)]
        if sub.empty:
            return dict.fromkeys(["B口", "S口", "B金", "S金", "B未口", "S未口", "B未金", "S未金"], 0)
        r = sub.iloc[0]
        return {
            "B口": _to_int(r[long_lot_col]),  "S口": _to_int(r[short_lot_col]),
            "B金": _to_int(r[long_amt_col]),  "S金": _to_int(r[short_amt_col]),
            "B未口": _to_int(r[long_oi_lot_col]), "S未口": _to_int(r[short_oi_lot_col]),
            "B未金": _to_int(r[long_oi_amt_col]), "S未金": _to_int(r[short_oi_amt_col]),
        }

    f_call = pick("外資", "CALL")
    f_put = pick("外資", "PUT")
    d_call = pick("自營", "CALL")
    d_put = pick("自營", "PUT")

    # 三大法人 (自營+投信+外資) 買權/賣權「買方」未平倉口數與金額加總。
    call_rows = df[df[cp_col].astype(str).str.upper().str.contains("CALL|買權", na=False)]
    put_rows = df[df[cp_col].astype(str).str.upper().str.contains("PUT|賣權", na=False)]
    inst_call_buy_lot = call_rows[long_oi_lot_col].apply(_to_int).sum()
    inst_call_buy_amt = call_rows[long_oi_amt_col].apply(_to_int).sum()
    inst_put_buy_lot = put_rows[long_oi_lot_col].apply(_to_int).sum()
    inst_put_buy_amt = put_rows[long_oi_amt_col].apply(_to_int).sum()

    # BC=多方未平倉 (Buy Call OI), SC=空方未平倉 (Sell Call OI)
    # BP=多方未平倉 (Buy Put OI),  SP=空方未平倉 (Sell Put OI)
    return {
        "外資BC口數": f_call["B未口"], "外資SC口數": f_call["S未口"],
        "外資BC金額": f_call["B未金"], "外資SC金額": f_call["S未金"],
        "外資BP口數": f_put["B未口"],  "外資SP口數": f_put["S未口"],
        "外資BP金額": f_put["B未金"],  "外資SP金額": f_put["S未金"],
        "外資買方買權金額": f_call["B未金"],
        "外資買方賣權金額": f_put["B未金"],
        "外資(買)OP未平倉金額": f_call["B未金"] - f_call["S未金"],
        "外資(賣)OP未平倉金額": f_put["B未金"] - f_put["S未金"],

        "自營BC口數": d_call["B未口"], "自營SC口數": d_call["S未口"],
        "自營BC金額": d_call["B未金"], "自營SC金額": d_call["S未金"],
        "自營BP口數": d_put["B未口"],  "自營SP口數": d_put["S未口"],
        "自營BP金額": d_put["B未金"],  "自營SP金額": d_put["S未金"],
        "自營買方買權金額": d_call["B未金"],
        "自營買方賣權金額": d_put["B未金"],
        "自營(買)OP未平倉金額": d_call["B未金"] - d_call["S未金"],
        "自營(賣)OP未平倉金額": d_put["B未金"] - d_put["S未金"],

        "三大法人買權買方未平倉口數": inst_call_buy_lot,
        "三大法人賣權買方未平倉口數": inst_put_buy_lot,
        "今日三大法人(買)OP未平倉金額": inst_call_buy_amt,
        "今日三大法人(賣)OP未平倉金額": inst_put_buy_amt,
    }


# 臺指選擇權每口契約價值乘數 (NT$50/點)。optDataDown 無未平倉金額欄，
# 以「未沖銷契約數 × 結算價 × 50」推估全市場未平倉金額。
TXO_MULTIPLIER = 50
OPT_DAILY_URL = "https://www.taifex.com.tw/cht/3/optDataDown"


def fetch_market_op_oi(date_yyyymmdd: str):
    """全市場 (含散戶) 臺指選擇權買權/賣權未沖銷契約量與推估未平倉金額。"""
    y, m, d = date_yyyymmdd[:4], date_yyyymmdd[4:6], date_yyyymmdd[6:8]
    form = {
        "down_type": "1",
        "commodity_id": "TXO",
        "queryStartDate": f"{y}/{m}/{d}",
        "queryEndDate": f"{y}/{m}/{d}",
        "MarketCode": "0",
    }
    r = requests.post(OPT_DAILY_URL, data=form, headers=HEADERS, timeout=30, verify=False)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.content.decode("ms950", errors="replace")), index_col=False)
    df.columns = [c.strip() for c in df.columns]

    contract_col = next((c for c in df.columns if c == "契約"), None)
    cp_col = next((c for c in df.columns if "買賣權" in c), None)
    month_col = next((c for c in df.columns if "到期月份" in c), None)
    session_col = next((c for c in df.columns if "交易時段" in c), None)
    oi_col = next((c for c in df.columns if "未沖銷契約數" in c), None)
    settle_col = next((c for c in df.columns if c == "結算價"), None)

    if not all([contract_col, cp_col, month_col, session_col, oi_col, settle_col]):
        raise RuntimeError(f"TAIFEX 選擇權每日 CSV 欄位缺漏: {list(df.columns)}")

    sub = df[(df[contract_col].astype(str).str.strip() == "TXO")
             & (df[session_col].astype(str).str.strip() == "一般")].copy()
    # 排除價差單 (到期月份含 /)
    sub = sub[~sub[month_col].astype(str).str.contains("/", na=False)]
    sub["_cp"] = sub[cp_col].astype(str).str.strip()
    sub["_oi"] = sub[oi_col].apply(_to_int)
    sub["_sp"] = sub[settle_col].apply(lambda v: _to_float(v) or 0.0)

    call = sub[sub["_cp"].str.contains("買權|CALL", case=False, na=False)]
    put = sub[sub["_cp"].str.contains("賣權|PUT", case=False, na=False)]

    call_oi = int(call["_oi"].sum())
    put_oi = int(put["_oi"].sum())
    # 推估金額 = Σ(未沖銷 × 結算價 × 50) 元，再 /1000 轉仟元，與三大法人金額單位一致。
    call_amt = int((call["_oi"] * call["_sp"] * TXO_MULTIPLIER).sum() / 1000)
    put_amt = int((put["_oi"] * put["_sp"] * TXO_MULTIPLIER).sum() / 1000)

    return {
        "全市場買權未沖銷": call_oi,
        "全市場賣權未沖銷": put_oi,
        "今日市場(買)OP未平倉金額": call_amt,
        "今日市場(賣)OP未平倉金額": put_amt,
    }


def _fetch_per_month_oi(date_yyyymmdd: str, commodity_id: str):
    """回傳 (當月OI, 次月OI, 全市場OI) — 全市場 = 各到期月份合計，排除價差與週選。"""
    y, m, d = date_yyyymmdd[:4], date_yyyymmdd[4:6], date_yyyymmdd[6:8]
    form = {
        "down_type": "1",
        "commodity_id": commodity_id,
        "queryStartDate": f"{y}/{m}/{d}",
        "queryEndDate": f"{y}/{m}/{d}",
        "MarketCode": "0",
    }
    r = requests.post(TX_DAILY_URL, data=form, headers=HEADERS, timeout=30, verify=False)
    r.raise_for_status()
    text = r.content.decode("ms950", errors="replace")
    # CSV 資料行尾多一個逗號，欄位數比 header 多 1 → 必須 index_col=False 避免 pandas 把首欄誤當 index。
    df = pd.read_csv(io.StringIO(text), index_col=False)
    df.columns = [c.strip() for c in df.columns]

    contract_col = next((c for c in df.columns if c == "契約"), None)
    month_col = next((c for c in df.columns if "到期月份" in c), None)
    session_col = next((c for c in df.columns if "交易時段" in c), None)
    oi_col = next((c for c in df.columns if "未沖銷契約數" in c), None)

    if not all([contract_col, month_col, session_col, oi_col]):
        raise RuntimeError(f"{commodity_id} 每日 CSV 欄位缺漏: {list(df.columns)}")

    sub = df[(df[contract_col].astype(str).str.strip() == commodity_id)
             & (df[session_col].astype(str).str.strip() == "一般")].copy()
    sub["_month"] = sub[month_col].astype(str).str.strip()

    # 全市場「小計」=一般時段、排除價差單(/)、含週選(W) 的未沖銷契約數加總，
    # 與期交所「期貨每日交易行情查詢」頁面顯示的小計一致。
    no_spread = sub[~sub["_month"].str.contains("/", na=False)]
    total_oi = no_spread[oi_col].apply(_to_int).sum()

    # 當月 / 次月只取月選 (排除週選 W)，依到期月份排序取最近兩個。
    monthly = no_spread[~no_spread["_month"].str.contains("W", na=False)].sort_values("_month")
    front_oi = _to_int(monthly.iloc[0][oi_col]) if len(monthly) >= 1 else 0
    next_oi = _to_int(monthly.iloc[1][oi_col]) if len(monthly) >= 2 else 0
    return front_oi, next_oi, total_oi


def fetch_tx_per_month_oi(date_yyyymmdd: str):
    """大台 / 小台 / 微台 各到期月份未沖銷契約量 — 取當月、次月、全市場合計。"""
    tx_front, tx_next, _ = _fetch_per_month_oi(date_yyyymmdd, "TX")
    mtx_front, mtx_next, mtx_total = _fetch_per_month_oi(date_yyyymmdd, "MTX")
    tmf_front, tmf_next, tmf_total = _fetch_per_month_oi(date_yyyymmdd, "TMF")
    # 期貨「多單 OI」=「空單 OI」=全市場合計 (一買一賣)。
    return {
        "當月大台未沖銷契約量": tx_front,
        "次月大台未沖銷契約量": tx_next,
        "當月小台未沖銷契約量": mtx_front,
        "次月小台未沖銷契約量": mtx_next,
        "當月微台未沖銷契約量": tmf_front,
        "次月微台未沖銷契約量": tmf_next,
        "小台未沖銷契約量": mtx_total,
        "微台未沖銷契約量": tmf_total,
    }


def fetch_pcr(date_yyyymmdd: str):
    """臺指選擇權 Put/Call Ratio — 成交量比與未平倉量比 (%)。"""
    y, m, d = date_yyyymmdd[:4], date_yyyymmdd[4:6], date_yyyymmdd[6:8]
    form = {"queryStartDate": f"{y}/{m}/{d}", "queryEndDate": f"{y}/{m}/{d}"}
    r = requests.post(PCR_URL, data=form, headers=HEADERS, timeout=30, verify=False)
    r.raise_for_status()
    text = r.content.decode("ms950", errors="replace")
    df = pd.read_csv(io.StringIO(text), index_col=False)
    df.columns = [c.strip() for c in df.columns]

    if df.empty:
        return {"PCR成交量比": None, "PCR未平倉比": None}

    vol_col = next((c for c in df.columns if "成交量比率" in c), None)
    oi_col = next((c for c in df.columns if "未平倉量比率" in c), None)
    if not (vol_col and oi_col):
        raise RuntimeError(f"PCR CSV 欄位缺漏: {list(df.columns)}")

    row = df.iloc[0]
    def f(v):
        try:
            return float(str(v).replace(",", "").strip())
        except (ValueError, AttributeError):
            return None

    return {"PCR成交量比": f(row[vol_col]), "PCR未平倉比": f(row[oi_col])}
