import yfinance as yf
import json
import os
from datetime import datetime

SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'TSLA']
os.makedirs('docs/data', exist_ok=True)

for sym in SYMBOLS:
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period='30d', interval='1d')
        if df.empty:
            print(f'❌ {sym} 无数据')
            continue

        data = []
        for index, row in df.iterrows():
            data.append({
                "t": index.strftime('%Y-%m-%d'),
                "o": round(row['Open'], 2),
                "h": round(row['High'], 2),
                "l": round(row['Low'], 2),
                "c": round(row['Close'], 2),
                "v": int(row['Volume'])
            })

        out_path = f'docs/data/{sym.upper()}.json'
        with open(out_path, 'w') as f:
            json.dump(data, f, separators=(',', ':'))
        print(f'✅ {sym} -> {out_path} ({len(data)} 筆)')
    except Exception as e:
        print(f'❌ {sym} 失败: {e}')
