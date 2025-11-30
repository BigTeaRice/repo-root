from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 假設前端需要此 API，用於本地/Codespaces 運行或部署到雲服務器
app = FastAPI(title="Stock Data API")

# 允许前端域名跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境请指定具体域名）
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_hk_stock_data(symbol: str, days: int):
    """
    從 Yahoo Finance 獲取港股或美股的 OHLCV 數據，並計算技術指標。
    yfinance 港股代碼格式：00700.HK → 0700.HK（需去掉前導零）
    """
    # 處理港股代碼前導零
    yahoo_symbol = symbol
    if symbol.endswith('.HK') and symbol.startswith('00'):
        yahoo_symbol = symbol.replace('00', '0', 1)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    try:
        # 下載數據 (間隔 1 天)
        df = yf.download(
            yahoo_symbol,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if df.empty:
            raise ValueError(f"No data found for {symbol} in the specified range.")

        # --- 計算技術指標（與前端邏輯保持一致，便於對比）---
        # 簡單移動平均 (SMA)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()

        # 布林帶 (Bollinger Bands, BB)
        df['StdDev'] = df['Close'].rolling(window=20).std()
        df['UB'] = df['MA20'] + (2 * df['StdDev'])
        df['LB'] = df['MA20'] - (2 * df['StdDev'])

        # 格式化輸出
        results = []
        for index, row in df.iterrows():
            # 使用 .iloc[-1] 來獲取當日 OHLCV 的上一個交易日的收盤價
            prev_close = df['Close'].shift(1).loc[index]

            # 簡化十字星 (Doji) 判斷: Open ≈ Close
            doji = abs(row['Open'] - row['Close']) < (row['High'] - row['Low']) * 0.1

            results.append({
                "t": index.strftime('%Y-%m-%d'),  # 日期時間
                "o": round(row['Open'], 2),       # 開盤價
                "h": round(row['High'], 2),       # 最高價
                "l": round(row['Low'], 2),        # 最低價
                "c": round(row['Close'], 2),      # 收盤價
                "v": int(row['Volume']),          # 成交量
                "ma5": round(row['MA5'], 2) if pd.notna(row['MA5']) else None,
                "ma10": round(row['MA10'], 2) if pd.notna(row['MA10']) else None,
                "ma20": round(row['MA20'], 2) if pd.notna(row['MA20']) else None,
                "ub": round(row['UB'], 2) if pd.notna(row['UB']) else None,
                "lb": round(row['LB'], 2) if pd.notna(row['LB']) else None,
                # RSI/MACD/ATR 複雜，暫不計算，交給前端處理，後端主要提供 OHLCV
                "rsi": None,
                "macd": None,
                "atr": None,
                "doji": doji
            })
        
        # 移除前幾天的空值數據
        results = [r for r in results if r['t'] >= start_date.strftime('%Y-%m-%d')]

        return results

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        # 在 API 呼叫失敗時拋出 HTTP 500 錯誤，便於前端捕獲
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {e}")

@app.get("/api/kline")
async def kline_data(sym: str = "AAPL", range: str = "30d"):
    """
    獲取 K 線圖數據 (Open, High, Low, Close, Volume, Tech Indicators)
    範圍參數 (range) 需轉換為天數 (days)
    """
    range_map = {
        "1d": 2, "5d": 5, "30d": 30, "90d": 90, "180d": 180, "1y": 365
    }
    days = range_map.get(range, 30) # 默認 30 天

    # 為了確保 MA20 等計算，多拉取一些歷史數據
    fetch_days = days + 40
    
    return get_hk_stock_data(sym, fetch_days)

# 在生產環境中，請使用 uvicorn 啟動此應用
# uvicorn app:app --host 0.0.0.0 --port 5000
