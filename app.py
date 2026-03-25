from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """<!DOCTYPE html>
<html>
<head>
<meta charset=UTF-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
body{background:#060912;margin:0;font-family:sans-serif}
.wrap{padding:20px;max-width:480px;margin:0 auto}
.logo{text-align:center;padding:30px 0;font-size:2rem;font-weight:900;
background:linear-gradient(90deg,#FFD700,#00CFFF,#00FF88);
-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{text-align:center;color:#00CFFF;letter-spacing:4px;font-size:.75rem}
.badge{display:flex;align-items:center;justify-content:center;gap:8px;
margin:16px 0;color:#00FF88;font-size:.85rem}
.dot{width:8px;height:8px;background:#00FF88;border-radius:50%;
animation:pulse 1.5s infinite}
.card{background:#0d1628;border:1px solid rgba(0,207,255,.2);
border-radius:16px;padding:20px;margin:12px 0}
.row{display:flex;justify-content:space-between;padding:8px 0;
border-bottom:1px solid rgba(255,255,255,.05)}
.row:last-child{border-bottom:none}
.lbl{color:rgba(255,255,255,.4);font-size:.8rem}
.val{font-size:.9rem;font-weight:600}
.green{color:#00FF88}.gold{color:#FFD700}.blue{color:#00CFFF}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
.sig{background:#0d1628;border-radius:12px;padding:14px;text-align:center}
.sig.b{border:1px solid rgba(0,255,136,.3)}
.sig.s{border:1px solid rgba(255,68,102,.3)}
.sig.h{border:1px solid rgba(255,215,0,.3)}
.sig.w{border:1px solid rgba(0,207,255,.3)}
.ico{font-size:1.8rem;margin-bottom:6px}
.snm{font-size:.7rem;color:rgba(255,255,255,.4);margin-bottom:4px}
.sac{font-size:.85rem;font-weight:700}
.sig.b .sac{color:#00FF88}.sig.s .sac{color:#FF4466}
.sig.h .sac{color:#FFD700}.sig.w .sac{color:#00CFFF}
.spx{font-size:.75rem;color:rgba(255,255,255,.3);margin-top:4px}
.ticker{background:#0d1628;border:1px solid rgba(0,207,255,.2);
border-radius:12px;padding:12px;overflow:hidden;margin:12px 0}
.tick-in{display:flex;gap:20px;animation:scroll 15s linear infinite;white-space:nowrap}
.ti{display:inline-flex;gap:6px;font-size:.8rem}
.ts{color:#00CFFF;font-weight:600}.tu{color:#00FF88}.td{color:#FF4466}
.footer{text-align:center;color:rgba(255,255,255,.2);font-size:.7rem;
padding:20px 0;letter-spacing:2px}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
</style>
</head>
<body>
<div class=wrap>
<div class=logo>MATHAN AI</div>
<div class=sub>HEMAN TRADING ENGINE</div>
<div class=badge><span class=dot></span>LIVE SERVER</div>
<div class=card>
<div class=row><span class=lbl>STATUS</span><span class="val green">ACTIVE</span></div>
<div class=row><span class=lbl>SERVER</span><span class="val blue">127.0.0.1:5000</span></div>
<div class=row><span class=lbl>ENGINE</span><span class="val gold">MATHAN AI v1.0</span></div>
<div class=row><span class=lbl>MARKET</span><span class="val green">NSE / BSE</span></div>
</div>
<div class=grid>
<div class="sig b"><div class=ico>ðŸ“ˆ</div><div class=snm>NIFTY 50</div><div class=sac>BUY</div><div class=spx>22,450 â–²</div></div>
<div class="sig s"><div class=ico>ðŸ“‰</div><div class=snm>BANKNIFTY</div><div class=sac>SELL</div><div class=spx>48,200 â–¼</div></div>
<div class="sig h"><div class=ico>â¸ï¸</div><div class=snm>SENSEX</div><div class=sac>HOLD</div><div class=spx>73,800 â†’</div></div>
<div class="sig w"><div class=ico>ðŸ‘ï¸</div><div class=snm>MIDCAP</div><div class=sac>WATCH</div><div class=spx>42,100 â†º</div></div>
</div>
<div class=ticker><div class=tick-in>
<span class=ti><span class=ts>RELIANCE</span><span class=tu>â–²2,845</span></span>
<span class=ti><span class=ts>TCS</span><span class=td>â–¼3,920</span></span>
<span class=ti><span class=ts>INFY</span><span class=tu>â–²1,456</span></span>
<span class=ti><span class=ts>HDFC</span><span class=tu>â–²1,678</span></span>
<span class=ti><span class=ts>WIPRO</span><span class=td>â–¼456</span></span>
<span class=ti><span class=ts>RELIANCE</span><span class=tu>â–²2,845</span></span>
<span class=ti><span class=ts>TCS</span><span class=td>â–¼3,920</span></span>
</div></div>
<div class=footer>MATHAN AI HEMAN Â· TERMUX Â· 2026</div>
</div></body></html>"""

@app.route("/ping")
def ping():
    return '{"status":"OK","engine":"MATHAN AI HEMAN"}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)