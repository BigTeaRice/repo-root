#!/usr/bin/env python3
import json, os, pandas as pd, numpy as np, yfinance as yf, akshare as ak
from datetime import datetime

os.makedirs('docs/data', exist_ok=True)

STOCKS = {'AAPL': 'yfinance', '0700.HK': 'yfinance',
          '000001': 'akshare', 'MSFT': 'yfinance'}

def fetch_yf(sym, bar='15m'):
    df = yf.Ticker(sym).history(period='5d', interval=bar).reset_index()
    df = df.rename(columns=str.lower)[['datetime','open','high','low','close','volume']]
    return df

def fetch_ak(sym):
    ak_sym = ('sh' if sym.startswith('6') else 'sz') + sym
    df = ak.stock_zh_a_hist(symbol=ak_sym[2:], period='15',
                            start_date=(datetime.today()-pd.Timedelta(days=30)).strftime('%Y%m%d'),
                            end_date=datetime.today().strftime('%Y%m%d'), adjust='')
    df = df.rename(columns={'日期':'datetime','开盘':'open','最高':'high','最低':'low','收盘':'close','成交量':'volume'})
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

def ind(df):
    c = df['close']
    df['MA5'] = c.rolling(5).mean()
    df['MA20'] = c.rolling(20).mean()
    delta = c.diff()
    rs = delta.clip(lower=0).rolling(14).mean() / (-delta.clip(upper=0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + rs))
    ema12, ema26 = c.ewm(span=12).mean(), c.ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_S'] = df['MACD'].ewm(span=9).mean()
    return df

for sym, src in STOCKS.items():
    try:
        df = (fetch_yf(sym) if src == 'yfinance' else fetch_ak(sym))
        df = ind(df).dropna()
        payload = {'symbol': sym, 'source': src, 'updated': datetime.utcnow().isoformat()+'Z',
                   'data': df.to_dict(orient='records')}
        out = f"docs/data/{sym.lower().replace('.','_')}.json"
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, default=str)
        print(f'✅ {sym}  ->  {out}  ({len(df)} 筆)')
    except Exception as e:
        print(f'❌ {sym} 失敗: {e}')
