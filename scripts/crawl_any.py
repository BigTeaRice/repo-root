#!/usr/bin/env python3
import yfinance as yf,json,os,sys,datetime as dt

def fix(sym):return sym.replace("00","0",1)if sym.endswith(".HK")and sym.startswith("00")else sym
def crawl(sl,prd):
    os.makedirs('docs/data',exist_ok=True)
    for s in sl:
        s=s.strip().upper();yh=fix(s)
        try:
            df=yf.Ticker(yh).history(period=prd,interval='1d',prepost=False)
            if df.empty:print(f'❌{s}无数据');continue
            out=[{"t":t.strftime('%Y-%m-%d'),"o":round(float(row.Open),2),"h":round(float(row.High),2),"l":round(float(row.Low),2),"c":round(float(row.Close),2),"v":int(row.Volume)} for t,row in df.iterrows()]
            fn=s.replace(".","")+".json"
            with open(f'docs/data/{fn}','w')as f:json.dump(out,f,separators=(',',':'))
            print(f'✅{s}→{fn}共{len(out)}条')
        except Exception as e:print(f'❌{s}失败:{e}')
if __name__=='__main__':
    if len(sys.argv)<2:print("用法: python crawl_any.py AAPL,0700.HK,TSLA 30d");sys.exit(1)
    crawl(sys.argv[1].split(','),sys.argv[2]if len(sys.argv)>2 else'30d')
