"""將「籌碼資料.xlsx」3 個分頁匯出成前端用的 JSON。

輸出檔：
- data/raw.json      — 爬蟲資料分頁全部資料
- data/stats.json    — 統計分頁全部資料
- data/options.json  — 選擇權分頁全部資料
- data/latest.json   — 三分頁各取最後一筆 + updated_at metadata (給首頁快讀)

所有日期欄轉成 'YYYY-MM-DD' 字串；NaN 轉成 null。
"""
import json
import math
import os
from datetime import date, datetime

import pandas as pd

import excel_writer

XLSX_PATH = os.environ.get(
    "XLSX_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "籌碼資料.xlsx"),
)
OUTPUT_DIR = os.environ.get(
    "JSON_OUTPUT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),
)

SHEETS = {
    "raw": "爬蟲資料",
    "stats": "統計",
    "options": "選擇權",
}


def _clean_value(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    return v


def _df_to_records(df: pd.DataFrame):
    records = []
    for _, row in df.iterrows():
        records.append({col: _clean_value(val) for col, val in row.items()})
    return records


def _read_sheet(file_path: str, sheet_name: str) -> pd.DataFrame:
    header = excel_writer.detect_header_row(file_path, sheet_name)
    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype={"日期": str}, header=header)
    if "日期" in df.columns:
        df["日期"] = df["日期"].astype(str).str.slice(0, 10)
        df = df.dropna(subset=["日期"]).sort_values("日期").reset_index(drop=True)
    return df


def _dump_json(path: str, obj, compact=True):
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    if not os.path.exists(XLSX_PATH):
        raise FileNotFoundError(XLSX_PATH)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    bundle = {}
    latest = {}
    for key, sheet in SHEETS.items():
        df = _read_sheet(XLSX_PATH, sheet)
        records = _df_to_records(df)
        bundle[key] = records
        latest[key] = records[-1] if records else None
        _dump_json(os.path.join(OUTPUT_DIR, f"{key}.json"), records, compact=True)
        print(f"  {sheet}: {len(records)} rows → data/{key}.json")

    updated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    latest_payload = {
        "updated_at": updated_at,
        **latest,
    }
    _dump_json(os.path.join(OUTPUT_DIR, "latest.json"), latest_payload, compact=False)
    print(f"  latest snapshot → data/latest.json  (updated_at={updated_at})")


if __name__ == "__main__":
    main()
