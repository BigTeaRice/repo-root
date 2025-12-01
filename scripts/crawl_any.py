#!/usr/bin/env python3
"""
本地一次性爬任意股票
python scripts/crawl_any.py  AAPL,0700.HK,TSLA  30d
"""
import yfinance as yf, json, os, sys
from datetime import datetime

def fix_hk(sym: str):
    return sym.replace("00","0",1) if sym.endswith(".HK") and sym.startswith("00") else sym

def crawl(symbols, period):
    os.makedirs('docs/data', exist_ok=True)
    for s in symbols:
        s = s.strip().upper()
        y_sym = fix_hk(s)
        try:
            df = yf.Ticker(y_sym).history(period=period, interval='1d', prepost=False)
            if df.empty:
                print(f'❌ {s} 无数据'); continue
            out = [
                {
                    "t": t.strftime('%Y-%m-%d'),
                    "o": round(float(row.Open), 2),
                    "h": round(float(row.High), 2),
                    "l": round(float(row.Low), 2),
                    "c": round(float(row.Close), 2),
                    "v": int(row.Volume)
                }
                for t, row in df.iterrows()
            ]
            file_name = s.replace(".", "") + ".json"
            with open(f'docs/data/{file_name}', "w") as f:
                json.dump(out, f, separators=(",", ":"))
            print(f'✅ {s} → {file_name} 共 {len(out)} 条')
        except Exception as e:
            print(f'❌ {s} 失败: {e}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python crawl_any.py AAPL,0700.HK,TSLA 30d")
        sys.exit(1)
    symbols = sys.argv[1].split(",")
    period  = sys.argv[2] if len(sys.argv) > 2 else "30d"
    crawl(symbols, period)
