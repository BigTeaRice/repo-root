from http.server import BaseHTTPRequestHandler
import yfinance as yf, json, urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.parse_qs(self.path.split('?')[-1])
        sym = query.get('sym', ['AAPL'])[0].upper()
        rng = query.get('range', ['30d'])[0]
        yh = sym.replace("00", "0", 1) if sym.endswith(".HK") and sym.startswith("00") else sym
        try:
            df = yf.Ticker(yh).history(period=rng, interval='1d', prepost=False)
            if df.empty: raise RuntimeError("No data")
            out = [{"t": t.strftime('%Y-%m-%d'), "o": round(float(row.Open), 2),
                    "h": round(float(row.High), 2), "l": round(float(row.Low), 2),
                    "c": round(float(row.Close), 2), "v": int(row.Volume)}
                   for t, row in df.iterrows()]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(out).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
