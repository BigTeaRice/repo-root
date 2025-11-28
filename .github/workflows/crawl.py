import yfinance as yf
import json
import os

SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'TSLA']
os.makedirs('docs/data', exist_ok=True)

for sym in SYMBOLS:
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period='30d', interval='15m')
        if df.empty:
            print(f'❌ {sym} 无数据')
            continue
        close = df['Close'].dropna().tolist()
        out_path = f'docs/data/{sym.lower()}.json'
        with open(out_path, 'w') as f:
            json.dump(close, f, separators=(',', ':'))
        print(f'✅ {sym} -> {out_path} ({len(close)} 筆)')
    except Exception as e:
        print(f'❌ {sym} 失败: {e}')
