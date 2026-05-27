import os
import sys
from datetime import datetime

import twse
import taifex
import excel_writer
import stats
import option_stats

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "籌碼資料.xlsx")

COLUMN_ORDER = [
    "日期",
    "當月大台未沖銷契約量", "次月大台未沖銷契約量",
    "當月小台未沖銷契約量", "次月小台未沖銷契約量",
    "當月微台未沖銷契約量", "次月微台未沖銷契約量",
    "加權指數", "加權指數漲跌", "加權指數當日高低差", "加權指數漲跌幅", "加權指數成交量",
    "融資金額", "融券",
    "外資現貨買賣超",
    "外資大台期貨未平倉", "外資小台期貨未平倉", "外資微台期貨未平倉",
    "外資BC口數", "外資BC金額", "外資SC口數", "外資SC金額",
    "外資BP口數", "外資BP金額", "外資SP口數", "外資SP金額",
    "外資買方買權金額", "外資買方賣權金額",
    "外資(買)OP未平倉金額", "外資(賣)OP未平倉金額",
    "自營(自行)現貨買賣超", "自營(避險)現貨買賣超",
    "自營大台期貨未平倉", "自營小台期貨未平倉", "自營微台期貨未平倉",
    "自營BC口數", "自營SC口數", "自營BC金額", "自營SC金額",
    "自營BP口數", "自營SP口數", "自營BP金額", "自營SP金額",
    "自營買方買權金額", "自營買方賣權金額",
    "自營(買)OP未平倉金額", "自營(賣)OP未平倉金額",
    "全市場買權未沖銷", "全市場賣權未沖銷",
    "三大法人買權買方未平倉口數", "三大法人賣權買方未平倉口數",
    "今日市場(買)OP未平倉金額", "今日市場(賣)OP未平倉金額",
    "今日三大法人(買)OP未平倉金額", "今日三大法人(賣)OP未平倉金額",
    "PCR成交量比", "PCR未平倉比",
    "小台未沖銷契約量",
    "三大法人多方小台口數", "三大法人空方小台口數",
    "微台未沖銷契約量",
    "三大法人多方微台口數", "三大法人空方微台口數",
]


def main(date_arg=None):
    target = date_arg or datetime.now().strftime("%Y%m%d")
    print(f"[{datetime.now():%H:%M:%S}] 抓取目標日期: {target}")

    print("  - TWSE 大盤指數...")
    idx = twse.fetch_index(target)
    trade_date = idx.pop("trade_date")
    trade_date_compact = trade_date.replace("-", "")
    print(f"    實際交易日: {trade_date}, 收盤 {idx['加權指數']}")

    print("  - TWSE 融資融券...")
    margin = twse.fetch_margin(trade_date_compact)

    print("  - TWSE 自營商現貨買賣超...")
    dealer = twse.fetch_dealer_spot(trade_date_compact)

    print("  - TAIFEX 三大法人期貨...")
    fut = taifex.fetch_futures(trade_date_compact)

    print("  - TAIFEX 三大法人選擇權...")
    opt = taifex.fetch_options(trade_date_compact)

    print("  - TAIFEX 大/小/微台各月份未沖銷...")
    tx_oi = taifex.fetch_tx_per_month_oi(trade_date_compact)

    print("  - TAIFEX 全市場選擇權未平倉...")
    mkt_op = taifex.fetch_market_op_oi(trade_date_compact)

    print("  - TAIFEX PCR...")
    pcr = taifex.fetch_pcr(trade_date_compact)

    row = {"日期": trade_date}
    row.update(idx)
    row.update(margin)
    row.update(dealer)
    row.update(fut)
    row.update(opt)
    row.update(tx_oi)
    row.update(mkt_op)
    row.update(pcr)

    missing = [c for c in COLUMN_ORDER if c not in row]
    if missing:
        print(f"  ⚠ 未填欄位: {missing}")

    print(f"  - 寫入 {OUTPUT_FILE}")
    excel_writer.append_row(OUTPUT_FILE, row, COLUMN_ORDER)

    print("  - 更新統計頁 (僅當日列)...")
    stats.recalculate(OUTPUT_FILE, target_dates=[trade_date])

    print("  - 更新選擇權頁 (僅當日列)...")
    option_stats.recalculate(OUTPUT_FILE, target_dates=[trade_date])

    print(f"[{datetime.now():%H:%M:%S}] 完成 ({trade_date})。共 {len(COLUMN_ORDER)} 欄 + 統計頁 + 選擇權頁。")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg)
