#!/usr/bin/env python3
"""
一键更新任意美股/港股日线 JSON（本地 & GitHub Actions 两用）
用法：
    # 本地
    python scripts/crawl_any.py AAPL,0700.HK,TSLA 90d

    # GitHub Actions 里内嵌
    python $GITHUB_WORKSPACE/scripts/crawl_any.py "${{ github.event.inputs.symbols }}" "${{ github.event.inputs.period }}"
"""
import yfinance as yf
import json
import os
import sys


def fix_symbol(sym: str) -> str:
    """港股 00700.HK → 0700.HK（去掉前导 00）"""
    if sym.endswith(".HK") and sym.startswith("00"):
        return sym.replace("00", "0", 1)
    return sym


def crawl(symbols: list[str], period: str):
    """爬取并写入 docs/data/<SYM>.json"""
    os.makedirs("docs/data", exist_ok=True)
    for s in symbols:
        s = s.strip().upper()
        yh = fix_symbol(s)
        try:
            # period 參數支持 1d, 5d, 30d, 90d, 180d, 1y 等
            df = yf.Ticker(yh).history(period=period, interval="1d", prepost=False)
            if df.empty:
                print(f"❌ {s} 无数据"); continue

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

            # 修正：直接使用完整的股票代碼作為文件名的一部分，例如：0700.HK.json
            file_name = s + ".json"
            with open(f"docs/data/{file_name}", "w") as f:
                # 使用 separators=(",", ":") 減少 JSON 文件大小
                json.dump(out, f, separators=(",", ":"))
            print(f"✅ {s} → {file_name} 共 {len(out)} 条")
        except Exception as e:
            print(f"❌ {s} 失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python crawl_any.py AAPL,0700.HK,TSLA 90d")
        sys.exit(1)

    raw_symbols = sys.argv[1].split(",")
    # 週期默認為 30 天
    period = sys.argv[2] if len(sys.argv) > 2 else "30d" 
    crawl(raw_symbols, period)
