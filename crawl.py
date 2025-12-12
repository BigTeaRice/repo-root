#!/usr/bin/env python3
import os, sys, time, random, json
import yfinance as yf
# ====== 备用：Alpha Vantage（只需把下面两行取消注释并填 key）======
# from alpha_vantage.timeseries import TimeSeries
# ts = TimeSeries(key=os.getenv('ALPHA_KEY'), output_format='pandas')

def robust_yahoo(sym: str, period: str, retries=3):
    """带重试 + 随机延迟，降低被封概率"""
    for i in range(retries):
        try:
            time.sleep(random.uniform(0, 2))
            df = yf.Ticker(sym).history(period=period, interval='1d', prepost=False, timeout=30)
            if not df.empty:
                return df
        except Exception as e:
            print(f"重试 {i+1}/3 失败: {e}")
    return None


def crawl(symbols: list[str], period: str):
    os.makedirs("docs/data", exist_ok=True)
    for s in symbols:
        s = s.strip().upper()
        yh = s.replace("00", "0", 1) if s.endswith(".HK") and s.startswith("00") else s
        try:
            df = robust_yahoo(yh, period)
            if df is None or df.empty:
                # ====== 备用：Alpha Vantage fallback ======
                # df = ts.get_daily_adjusted(symbol=s, outputsize='full')[0]
                # df = df.tail(_parse_days(period))   # 简单截断
                print(f"❌ {s} 无数据"); continue

            out = [
                {
                    "t": t.strftime('%Y-%m-%d'),
                    "o": round(float(row.Open), 2),
                    "h": round(float(row.High), 2),
                    "l": round(float(row.Low), 2),
                    "c": round(float(row.Close), 2),
                    "v": int(row.Volume),
                }
                for t, row in df.iterrows()
            ]

            file_name = s.replace(".", "") + ".json"
            with open(f"docs/data/{file_name}", "w") as f:
                json.dump(out, f, separators=(",", ":"))
            print(f"✅ {s} → {file_name} 共 {len(out)} 条")
        except Exception as e:
            print(f"❌ {s} 失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python crawl.py AAPL,0700.HK,TSLA 90d")
        sys.exit(1)
    crawl(sys.argv[1].split(","), sys.argv[2] if len(sys.argv) > 2 else "30d")
