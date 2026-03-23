"""
MATHAN AI — ANGEL ONE FULL INTEGRATION
========================================
Fixed version for Render Free Tier (No WebSocket, HTTP Polling only)
"""

import os, json, time, threading, datetime, socket, requests, sqlite3
import pyotp
try:
    from SmartApi import SmartConnect
    SMARTAPI_OK = True
except ImportError:
    SMARTAPI_OK = False
from flask import Flask, Response, jsonify, request

# ── DASHBOARD HTML ────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<title>Mathan AI — Angel One Brain</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#070b0f;--bg2:#0d1419;--bg3:#111820;--brd:#1e2d3d;
  --gold:#f0a500;--grn:#00e676;--red:#ff1744;--blu:#29b6f6;
  --pur:#ce93d8;--orn:#ff9800;--txt:#cdd9e5;--dim:#4a6278;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--txt);font-family:'Rajdhani',sans-serif;padding-bottom:40px;}
.hdr{position:sticky;top:0;z-index:100;background:linear-gradient(180deg,#0a1118,rgba(7,11,15,.97));border-bottom:2px solid var(--gold);padding:10px 14px;display:flex;align-items:center;justify-content:space-between;}
.logo{font-family:'Orbitron';font-size:11px;font-weight:900;color:var(--gold);letter-spacing:1px;}
.hclock{font-family:'Orbitron';font-size:12px;color:var(--gold);}
.main{padding:10px;max-width:480px;margin:0 auto;}
.card{background:var(--bg2);border:1px solid var(--brd);border-radius:12px;padding:12px;margin-bottom:9px;}
.inp{width:100%;background:var(--bg3);border:1px solid var(--brd);border-radius:6px;color:var(--txt);padding:8px 10px;font-size:12px;margin-bottom:6px;}
.cbtn{width:100%;padding:11px;border-radius:8px;cursor:pointer;font-family:'Orbitron';font-size:9px;border:1px solid var(--orn);background:rgba(255,152,0,.08);color:var(--orn);}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">MATHAN AI — ANGEL ONE</div>
  <div class="hclock" id="clock">--:--:--</div>
</div>
<div class="main">
  <div class="card">
    <div style="color:var(--gold);font-size:12px;margin-bottom:10px;">ANGEL ONE LOGIN</div>
    <input class="inp" id="api-key" type="password" placeholder="API Key"/>
    <input class="inp" id="client-id" type="text" placeholder="Client ID"/>
    <input class="inp" id="angel-pin" type="password" placeholder="PIN"/>
    <input class="inp" id="totp-secret" type="password" placeholder="TOTP Secret"/>
    <button class="cbtn" onclick="connectAngel()">CONNECT</button>
  </div>
  <div id="status" style="color:var(--grn);font-family:'Share Tech Mono';font-size:12px;">Waiting...</div>
</div>
<script>
function connectAngel(){
  const data = {
    api_key: document.getElementById('api-key').value,
    client_id: document.getElementById('client-id').value,
    pin: document.getElementById('angel-pin').value,
    totp_secret: document.getElementById('totp-secret').value
  };
  fetch('/connect_angel', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  }).then(r => r.json()).then(j => {
    document.getElementById('status').textContent = j.msg || j.error;
  });
}
setInterval(()=>{
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();
},1000);
</script>
</body>
</html>"""

app = Flask(__name__)

# ── CONFIG ─────────────────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 8000))
DB = "/tmp/mathan_brain.db"

ANGEL = {"api_key":"","client_id":"","pin":"","totp_secret":"","connected":False}
SYS = {"source":"NONE","index":"NIFTY","count":0,"fetching":False}
M = {"spot":None,"atm":None,"pcr":None,"fetch_time":None}

# ── DATABASE ────────────────────────────────────────────────────────
def db_init():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT)")
    c.commit(); c.close()

def db_set(k, v):
    c = sqlite3.connect(DB)
    c.execute("INSERT OR REPLACE INTO config VALUES(?,?)", (k, str(v)))
    c.commit(); c.close()

def db_load():
    try:
        c = sqlite3.connect(DB)
        res = c.execute("SELECT * FROM config").fetchall()
        for k, v in res:
            if k.startswith("angel_"): ANGEL[k.replace("angel_","")] = v
        c.close()
    except: pass

# ── LOGIN LOGIC ─────────────────────────────────────────────────────
def do_angel_connect(api_key, client_id, pin, totp_secret):
    try:
        obj = SmartConnect(api_key=api_key)
        totp = pyotp.TOTP(totp_secret).now()
        data = obj.generateSession(client_id, pin, totp)
        if data['status']:
            ANGEL["connected"] = True
            db_set("angel_api_key", api_key)
            db_set("angel_client_id", client_id)
            db_set("angel_pin", pin)
            db_set("angel_totp_secret", totp_secret)
            print(f"SUCCESS: Connected to {client_id}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

# ── ROUTES ──────────────────────────────────────────────────────────
@app.route("/connect_angel", methods=["POST"])
def connect_angel_rest():
    d = request.get_json()
    threading.Thread(target=do_angel_connect, args=(d['api_key'], d['client_id'], d['pin'], d['totp_secret']), daemon=True).start()
    return jsonify({"ok":True, "msg":"Login process started"})

@app.route("/ping")
def ping():
    return jsonify({"status":"online", "time":datetime.datetime.now().strftime("%H:%M:%S")})

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return Response(DASHBOARD_HTML, mimetype="text/html")

if __name__ == "__main__":
    db_init()
    db_load()
    print(f"Starting server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
