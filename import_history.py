"""一次性匯入歷史統計資料到 籌碼資料.xlsx 的「統計」分頁。

來源檔: 籌碼表V3.0.xlsx「工作表1」(header on row 2)
目標檔: 籌碼資料.xlsx「統計」

匯入後會立即呼叫 stats.recalculate()，讓原始 sheet 內已有的日期以重算結果覆蓋
歷史值，其餘歷史日期照舊保留。
"""

import os
import warnings

import pandas as pd

import stats

warnings.filterwarnings("ignore")

DEFAULT_SOURCE = r"C:\Users\502029\Desktop\籌碼表V3.0.xlsx"
DEFAULT_TARGET = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "籌碼資料.xlsx"
)
SOURCE_SHEET = "工作表1"

# V3.0 欄名 → 統一 STATS_COLS 欄名
COLUMN_MAP = {
    "日期": "日期",
    "結算日": "結算日",
    "當次月大台留倉差增減": "當次月大台留倉差增減",
    "加權指數": "加權指數",
    "加權指數漲跌": "加權指數漲跌",
    "加權指數當日高低差": "加權指數當日高低差",
    "加權指數漲跌幅(%)": "加權指數漲跌幅(%)",
    "加權指數成交量(億)": "加權指數成交量(億)",
    "融資金額(仟元)": "融資金額(億)",       # 視為已是億
    "融資金額變化量": "融資金額變化量(億)",  # 視為已是億
    "融券(交易單位)": "融券(交易單位)",
    "融券單位變化量": "融券單位變化量",
    "PCR與結算比": "PCR與結算比",
    "外資現貨買賣超": "外資現貨買賣超",
    "外資(大小台)期貨未平倉": "外資(大小台)期貨未平倉",
    "外資期貨未平倉與結算比": "外資期貨未平倉與結算比",
    "外資期貨未平倉與前日增減": "外資期貨未平倉與前日增減",
    "外資(買)OP未平倉口數": "外資(買)OP未平倉口數",
    "外資(買)OP未平倉金額": "外資(買)OP未平倉金額",
    "外資(BC)OP未平倉金額與結算比": "外資(BC)OP未平倉金額與結算比",
    "外資(賣)OP未平倉口數": "外資(賣)OP未平倉口數",
    "外資(賣)OP未平倉金額": "外資(賣)OP未平倉金額",
    "外資(BP)OP未平倉金額與結算比": "外資(BP)OP未平倉金額與結算比",
    "外資買方買權/賣權比": "外資買方買權/賣權比",
    "外資買權/賣權比": "外資買權/賣權比",
    "自營(自行)現貨買賣超": "自營(自行)現貨買賣超",
    "自營(避險)現貨買賣超": "自營(避險)現貨買賣超",
    "自營(大小台)期貨未平倉": "自營(大小台)期貨未平倉",
    "自營(買)OP未平倉口數": "自營(買)OP未平倉口數",
    "自營(買)OP未平倉金額": "自營(買)OP未平倉金額",
    "自營(BC)OP未平倉金額與結算比": "自營(BC)OP未平倉金額與結算比",
    "自營(賣)OP未平倉口數": "自營(賣)OP未平倉口數",
    "自營(賣)OP未平倉金額": "自營(賣)OP未平倉金額",
    "自營(BP)OP未平倉金額與結算比": "自營(BP)OP未平倉金額與結算比",
    "自營買方買權/賣權比": "自營買方買權/賣權比",
    "散戶買/賣權比": "散戶買/賣權比",
    "散戶看多": "散戶看多",
    "散戶看空": "散戶看空",
    "當次月小台留倉差增減": "當次月小台留倉差增減",
    "散戶未平倉": "散戶未平倉",
    "微台散戶看多": "微台散戶看多",
    "微台散戶看空": "微台散戶看空",
    "微台散戶多空比": "微台散戶多空比",
    "微台散戶未平倉": "微台散戶未平倉",
    # 「當次月微台留倉差增減」V3.0 沒有 → 保留為 NaN
}


def load_history(source_path: str) -> pd.DataFrame:
    df = pd.read_excel(source_path, sheet_name=SOURCE_SHEET, header=1)
    # 重命名欄位
    df = df.rename(columns=COLUMN_MAP)
    # 補上目標 schema 中缺失的欄位
    for col in stats.STATS_COLS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[stats.STATS_COLS]

    # 日期 -> 'YYYY-MM-DD' 字串
    df["日期"] = pd.to_datetime(df["日期"]).dt.strftime("%Y-%m-%d")
    # 結算日 -> int (允許 NaN)
    df["結算日"] = pd.to_numeric(df["結算日"], errors="coerce").astype("Int64")

    # 移除日期空列
    df = df[df["日期"].notna() & (df["日期"] != "NaT")].reset_index(drop=True)
    return df


def main(source: str = DEFAULT_SOURCE, target: str = DEFAULT_TARGET):
    if not os.path.exists(source):
        raise FileNotFoundError(source)
    if not os.path.exists(target):
        raise FileNotFoundError(target)

    print(f"來源: {source}")
    print(f"目標: {target}")

    print("讀取歷史資料...")
    hist = load_history(source)
    print(f"  歷史列數: {len(hist)} (日期範圍: {hist['日期'].min()} ~ {hist['日期'].max()})")

    print("讀取目標檔現有「統計」分頁...")
    existing = stats._read_existing_stats(target)
    print(f"  現有列數: {len(existing)}")

    # 合併: existing 中的列 (已重算的當期值) 優先於歷史。
    if existing.empty:
        merged = hist
    else:
        keep_hist = hist[~hist["日期"].isin(set(existing["日期"]))]
        merged = pd.concat([keep_hist, existing], ignore_index=True)

    merged["_d"] = pd.to_datetime(merged["日期"])
    merged = merged.sort_values("_d").drop(columns=["_d"]).reset_index(drop=True)
    merged = merged[stats.STATS_COLS]

    print(f"合併後列數: {len(merged)}")
    print("寫入「統計」分頁並套樣式...")
    stats.write_stats_sheet(target, merged)

    print("以原始 sheet 重新計算覆蓋 (僅影響有原始資料的日期)...")
    stats.recalculate(target)

    print("完成。")


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    tgt = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TARGET
    main(src, tgt)
