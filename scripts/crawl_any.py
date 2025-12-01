#!/usr/bin/env python3
"""
一键更新任意美股/港股日线 JSON（本地 & GitHub Actions 两用）
- 若无参数传入（如 GitHub Actions 自动运行），则使用 DEFAULT_SYMBOLS 列表。
- 若有参数传入（如本地手动运行），则使用传入的代碼和週期。
"""
import yfinance as yf
import json
import os
import sys

# 【修正新增】定義一個固定的精選股票清單
DEFAULT_SYMBOLS = [
    "AAPL", "GOOGL", "TSLA", "MSFT", "NVDA",  # 美股热门
    "0700.HK", "9988.HK", "0005.HK", "3690.HK", # 港股热门
    "^GSPC", "^IXIC" # 主要指数
]

def fix_symbol(sym: str) -> str:
    """港股 00700.HK → 0700.HK（去掉前导 00）"""
    if sym.endswith(".HK") and sym.startswith("00"):
        return sym.replace("00", "0", 1)
    return sym


def crawl(symbols: list[str], period: str):
    """爬取并写入 docs/data/<SYM>.json"""
    # 確保 docs/data 目錄存在
    os.makedirs("docs/data", exist_ok=True)
    
    print(f"🎯 開始爬取 {len(symbols)} 支股票，週期: {period}")

    for s in symbols:
        s = s.strip().upper()
        # yfinance 符號修正（如 00700.HK → 0700.HK）
        yh = fix_symbol(s)
        try:
            # 使用 yfinance 獲取歷史數據
            df = yf.Ticker(yh).history(period=period, interval="1d", prepost=False)
            if df.empty:
                print(f"❌ {s} 无数据"); continue

            # 轉換為前端所需的 JSON 格式
            out = [
                {
                    "t": t.strftime("%Y-%m-%d"),
                    "o": round(float(row.Open), 2),
                    "h": round(float(row.High), 2),
                    "l": round(float(row.Low), 2),
                    "c": round(float(row.Close), 2),
                    "v": int(row.Volume),
                }
                for t, row in df.iterrows()
            ]

            # 保持原始命名規則：0700.HK → 0700HK.json
            file_name = s.replace(".", "") + ".json"  # 0700.HK → 0700HK.json
            with open(f"docs/data/{file_name}", "w") as f:
                # 使用 separators=(",", ":") 減少 JSON 文件大小
                json.dump(out, f, separators=(",", ":"))
            print(f"✅ {s} → {file_name} 共 {len(out)} 条")
        except Exception as e:
            print(f"❌ {s} 失败: {e}")


if __name__ == "__main__":
    # 【修正邏輯】如果沒有傳入參數 (如 GitHub Actions 自動運行)
    if len(sys.argv) < 2:
        print(f"未指定股票代碼，使用預設清單 ({len(DEFAULT_SYMBOLS)} 支).")
        raw_symbols = DEFAULT_SYMBOLS
        period = "1y" # 預設抓取 1 年數據
    else:
        # 如果有傳入參數 (如本地手動運行)
        raw_symbols = sys.argv[1].split(",")
        period = sys.argv[2] if len(sys.argv) > 2 else "30d"

    crawl(raw_symbols, period)
