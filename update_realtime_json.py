#!/usr/bin/env python3
"""
仅 yfinance → JSON（港股/美股 15min K）
输出：docs/data/<symbol>.json
"""
import os, json, pandas as pd, yfinance as yf
from datetime import datetime, timedelta

OUTPUT_DIR = "docs/data"
STOCKS = {'AAPL': 'US', '0700.HK': 'HK', 'MSFT': 'US', 'TSLA': 'US'}  # 仅港股/美股

def gmt_now():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def fetch_yf(sym, bar='15m', days=30):
    ticker = sym.replace('.HK', '')
    df = yf.Ticker(ticker).history(period=f'{days}d', interval=bar).reset_index()
    df = df.rename(columns=str.lower)[['datetime','open','high','low','close','volume']]
    return df

def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """前端全套技术指标"""
    c = df['close']
    df['MA5'] = c.rolling(5).mean()
    df['MA10'] = c.rolling(10).mean()
    df['MA20'] = c.rolling(20).mean()
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    hl = df['high'] - df['low']
    hcp = (df['high'] - c.shift()).abs()
    lcp = (df['low'] - c.shift()).abs()
    tr = pd.concat([hl, hcp, lcp], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['MTM'] = c / c.shift(12) - 1
    body = (df['close'] - df['open']).abs()
    hl2 = df['high'] - df['low']
    df['DOJI'] = (hl2 > 0) & (body / hl2 < 0.001)
    return df.dropna(thresh=5)   # 至少 5 栏有值即可

def main():
    os.makedirs("docs/data", exist_ok=True)
    for sym, region in STOCKS.items():
        try:
            df = fetch_yf(sym, bar='15m', days=30)
            df = calc_indicators(df)
            out = {"symbol": sym, "region": region, "updated": gmt_now(), "data": df.to_dict(orient='records')}
            file_name = sym.lower().replace('.', '_') + '.json'
            with open(f"docs/data/{file_name}", 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, default=str)
            print(f"✅ {sym}  ->  docs/data/{file_name}  ({len(df)} 筆)")
        except Exception as e:
            print(f"❌ {sym} 失敗: {e}")

    meta = {"build_time": gmt_now(), "stocks": list(STOCKS.keys())}
    with open("docs/data/meta.json", 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, default=str)
    print("=== 輸出完成 ===")

if __name__ == '__main__':
    main()
