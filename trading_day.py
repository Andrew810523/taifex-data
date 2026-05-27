"""判斷某日是否為台股交易日。

用法 (本機):
    python trading_day.py            # 看「今日」
    python trading_day.py 20260527   # 看指定日期

GitHub Actions 用法：寫入 $GITHUB_OUTPUT (is_trading=true/false, date=YYYYMMDD)。

假日清單需每年初手動補進 HOLIDAYS。
"""
import os
import sys
from datetime import date, datetime

# 台股休市日 (週六日自動排除、不需在此列出)。需每年補進新公告假日。
# 主要來源：TWSE 開休市日期 / TAIFEX 行事曆
HOLIDAYS = {
    # 2022
    date(2022, 1, 31), date(2022, 2, 1), date(2022, 2, 2), date(2022, 2, 3), date(2022, 2, 4),
    date(2022, 2, 28),
    date(2022, 4, 4), date(2022, 4, 5),
    date(2022, 5, 2),
    date(2022, 6, 3),
    date(2022, 9, 9),
    date(2022, 10, 10),
    # 2023
    date(2023, 1, 2),
    date(2023, 1, 20), date(2023, 1, 23), date(2023, 1, 24), date(2023, 1, 25),
    date(2023, 1, 26), date(2023, 1, 27),
    date(2023, 2, 27), date(2023, 2, 28),
    date(2023, 4, 3), date(2023, 4, 4), date(2023, 4, 5),
    date(2023, 5, 1),
    date(2023, 6, 22), date(2023, 6, 23),
    date(2023, 9, 29),
    date(2023, 10, 9), date(2023, 10, 10),
    # 2024
    date(2024, 1, 1),
    date(2024, 2, 8), date(2024, 2, 9), date(2024, 2, 12), date(2024, 2, 13), date(2024, 2, 14),
    date(2024, 2, 28),
    date(2024, 4, 4), date(2024, 4, 5),
    date(2024, 5, 1),
    date(2024, 6, 10),
    date(2024, 9, 17),
    date(2024, 10, 10),
    # 2025
    date(2025, 1, 1),
    date(2025, 1, 27), date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30), date(2025, 1, 31),
    date(2025, 2, 28),
    date(2025, 4, 3), date(2025, 4, 4),
    date(2025, 5, 1),
    date(2025, 5, 30),
    date(2025, 10, 6),
    date(2025, 10, 10),
    # 2026
    date(2026, 1, 1),
    date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 2, 19), date(2026, 2, 20),
    date(2026, 2, 27),
    date(2026, 4, 3), date(2026, 4, 6),
    date(2026, 5, 1),
    date(2026, 6, 19),
    date(2026, 9, 25),
    date(2026, 10, 9),
    # 2027 — TODO: 待 TWSE 公告後補進
}


def is_trading_day(d: date) -> bool:
    if d.weekday() >= 5:  # 5=Sat, 6=Sun
        return False
    if d in HOLIDAYS:
        return False
    return True


def _emit_github_output(key, value):
    out_path = os.environ.get("GITHUB_OUTPUT")
    if out_path:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main():
    arg = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() else ""
    if arg:
        target = datetime.strptime(arg, "%Y%m%d").date()
    else:
        target = date.today()

    td = is_trading_day(target)
    date_str = target.strftime("%Y%m%d")

    _emit_github_output("is_trading", "true" if td else "false")
    _emit_github_output("date", date_str)

    print(f"{target.isoformat()} ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][target.weekday()]}): "
          f"{'交易日' if td else '非交易日'}")
    # Exit 0 either way — let workflow decide via outputs
    sys.exit(0)


if __name__ == "__main__":
    main()
