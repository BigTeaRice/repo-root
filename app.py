# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)  # 允许前端跨域

@app.route('/api/kline', methods=['GET'])
def kline():
    symbol = request.args.get('sym', 'AAPL')
    period = request.args.get('range', '30d')
    interval = {'1d':'15m','5d':'15m','30d':'1h','90d':'1d','180d':'1d','1y':'1d'}.get(period,'1h')

    df = yf.download(symbol, period=period, interval=interval, progress=False)
    df.reset_index(inplace=True)
    df.rename(columns={'Open':'o','High':'h','Low':'l','Close':'c','Volume':'v'}, inplace=True)
    df['t'] = df.index.astype(str)  # 时间字符串

    # 计算指标
    df['ma5']  = df['c'].rolling(5).mean()
    df['ma10'] = df['c'].rolling(10).mean()
    df['ma20'] = df['c'].rolling(20).mean()
    df['rsi']  = df['c'].rolling(14).apply(lambda x: 100 - 100/(1+(x.diff().clip(lower=0).mean()/x.diff().clip(upper=0).abs().mean())))
    df['atr']  = df[['h','l','c']].apply(lambda row: max(row['h']-row['l'], abs(row['h']-row['c']), abs(row['l']-row['c'])), axis=1).rolling(14).mean()
    df['macd'], df['macdSignal'], _ = ta.MACD(df['c'], 12, 26, 9)
    df['doji'] = (abs(df['o']-df['c']) / (df['h']-df['l'])) < 0.1

    # 返回 JSON
    return jsonify(df[['o','h','l','c','v','t','ma5','ma10','ma20','rsi','atr','macd','macdSignal','doji']].dropna().to_dict(orient='records'))
