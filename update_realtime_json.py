#!/usr/bin/env python3
"""
实时行情 → JSON（GitHub Actions / 本地通用）
- Yahoo Finance：美股、港股 15min K
- AkShare：深圳、上海 日 K（保底 30+5 天，节假不空）
- 输出：docs/data/<symbol>.json
"""
import os
import json
import pandas as pd
import yfinance as yf
import akshare as ak
from datetime import datetime, timedelta

OUTPUT_DIR = "docs/data"
STOCKS = {
    'AAPL': 'yfinance',
    '0700.HK': 'yfinance',
    '000001': 'akshare',
    'MSFT': 'yfinance',
}
BAR_US_HK = '15m'          # Yahoo 15 分钟
BAR_CN = 'daily'           # AkShare 日 K
DEEP_DAYS = 30 + 5         # 保底 30 日 + 5 天保险

def ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def gmt_now():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def fetch_yf(sym, bar='15m', days=30):
    """Yahoo Finance 15min K"""
    ticker = sym.replace('.HK', '')
    df = yf.Ticker(ticker).history(period=f'{days}d', interval=bar).reset_index()
    df = df.rename(columns=str.lower)[['datetime','open','high','low','close','volume']]
    return df

def fetch_ak(sym, bar='daily', days=DEEP_DAYS) -> pd.DataFrame:
    """AkShare 日 K（保底 30+5 天，节假不空）"""
    ak_sym = ('sh' if sym.startswith('6') else 'sz') + sym
    end = datetime.now()
    start = end - timedelta(days=days)
    df = ak.stock_zh_a_hist(symbol=ak_sym[2:],
                            period=bar,
                            start_date=start.strftime('%Y%m%d'),
                            end_date=end.strftime('%Y%m%d'),
                            adjust='')
    if df.empty:
        raise RuntimeError(f"AkShare 回傳空 DataFrame（節假日無資料）：{sym}")
    df = df.rename(columns={'日期': 'datetime', '开盘': 'open', '最高': 'high',
                            '最低': 'low', '收盘': 'close', '成交量': 'volume'})
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """前端全套技术指标"""
    c = df['close']
    df['MA5'] = c.rolling(5).mean()
    df['MA10'] = c.rolling(10).mean()
    df['MA20'] = c.rolling(20).mean()
    # RSI(14)
    delta = c.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    # ATR(14)
    hl = df['high'] - df['low']
    hcp = (df['high'] - c.shift()).abs()
    lcp = (df['low'] - c.shift()).abs()
    tr = pd.concat([hl, hcp, lcp], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    # MTM(12)
    df['MTM'] = c / c.shift(12) - 1
    # Doji
    body = (df['close'] - df['open']).abs()
    hl2 = df['high'] - df['low']
    df['DOJI'] = (hl2 > 0) & (body / hl2 < 0.001)
    return df.dropna(thresh=5)   # 至少 5 栏有值即可

def main():
    ensure_dir()
    for sym, src in STOCKS.items():
        try:
            if src == 'yfinance':
                df = fetch_yf(sym, bar=BAR_US_HK, days=30)
            else:
                df = fetch_ak(sym, bar=BAR_CN, days=DEEP_DAYS)
            df = calc_indicators(df)
            out = {
                "symbol": sym,
                "source": src,
                "updated": gmt_now(),
                "data": df.to_dict(orient='records')
            }
            file_name = sym.lower().replace('.', '_') + '.json'
            with open(os.path.join(OUTPUT_DIR, file_name), 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, default=str)
            print(f"✅ {sym}  ->  {OUTPUT_DIR}/{file_name}  ({len(df)} 筆)")
        except Exception as e:
            print(f"❌ {sym} 失敗: {e}")

    # meta 文件
    meta = {"build_time": gmt_now(), "stocks": list(STOCKS.keys())}
    with open(os.path.join(OUTPUT_DIR, "meta.json"), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, default=str)
    print("=== 輸出完成 ===")

if __name__ == '__main__':
    main()
