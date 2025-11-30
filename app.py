from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import ta

app = Flask(__name__)
CORS(app)

@app.route('/api/kline', methods=['GET'])
def kline():
    symbol = request.args.get('sym', 'AAPL')
    period = request.args.get('range', '30d')
    interval = {'1d':'15m','5d':'15m','30d':'1h','90d':'1d','180d':'1d','1y':'1d'}.get(period,'1h')

    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df.empty: return jsonify([])

    df.reset_index(inplace=True)
    df.rename(columns={'Open':'o','High':'h','Low':'l','Close':'c','Volume':'v'}, inplace=True)
    df['t'] = df.index.astype(str)

    # 技术指标
    df['ma5']  = df['c'].rolling(5).mean()
    df['ma10'] = df['c'].rolling(10).mean()
    df['ma20'] = df['c'].rolling(20).mean()
    df['rsi']  = ta.momentum.RSIIndicator(df['c'], window=14).rsi()
    df['atr']  = ta.volatility.AverageTrueRange(df['h'], df['l'], df['c'], window=14).average_true_range()
    macd = ta.trend.MACD(df['c'])
    df['macd'] = macd.macd()
    df['macdSignal'] = macd.macd_signal()
    df['doji'] = (abs(df['o']-df['c']) / (df['h']-df['l'])) < 0.1

    out = df[['o','h','l','c','v','t','ma5','ma10','ma20','rsi','atr','macd','macdSignal','doji']].dropna()
    return jsonify(out.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
