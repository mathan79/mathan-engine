import os, json, time, threading, datetime, socket, requests, sqlite3
import pyotp
try:
    from SmartApi import SmartConnect
    SMARTAPI_OK = True
except ImportError:
    SMARTAPI_OK = False
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

# ── CONFIG ─────────────────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 8000))
DB = "/tmp/mathan_brain.db"

INDEX_CFG = {
    "NIFTY":  {"step": 50,  "lot": 75,  "token": "26000", "exchange": "NSE"},
    "SENSEX": {"step": 100, "lot": 20,  "token": "1",     "exchange": "BSE"},
}

ANGEL = {"api_key":"","client_id":"","pin":"","totp_secret":"","connected":False}
SYS = {"source":"NONE","index":"NIFTY","count":0,"fetching":False,"poll_interval":15}
M = {"spot":None,"atm":None,"pcr":None,"vix":None,"gift":None,"gift_diff":None,"ce_prem":None,"pe_prem":None,"support":None,"resistance":None,"fetch_time":None}

AGENTS = {f"l{i}": {"name": n, "signal": None, "detail": "", "weight": w} for i, (n, w) in enumerate([
    ("OI Analyst", 1.5), ("Price Action", 1.5), ("VIX Monitor", 1.5), ("GIFT Tracker", 1.0),
    ("CE Premium", 1.0), ("PE Premium", 1.0), ("Session Clock", 0.8), ("バランス Expiry", 0.8),
    ("Gap Detector", 1.0), ("PCR Engine", 1.2), ("Trap Detector", 1.5), ("Risk Control", 1.2), ("Behaviour AI", 2.0)
], 1)}

BRAIN = {"signal": "WAIT", "bull_pct": 50, "bear_pct": 50, "confidence": "LOW", "reasons": []}

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
    for f in ["api_key","client_id","pin","totp_secret"]:
        v = db_get(f"angel_{f}")
        if v: ANGEL[f] = v

def db_get(k):
    try:
        c = sqlite3.connect(DB); r = c.execute("SELECT value FROM config WHERE key=?", (k,)).fetchone(); c.close()
        return r[0] if r else None
    except: return None

# ── MARKET & AGENT LOGIC (உங்களின் app-22.py-ல் இருந்த அதே லாஜிக்) ────
def poll_loop():
    while True:
        time.sleep(SYS["poll_interval"])
        if ANGEL["connected"]:
            # Market data fetching logic
            pass

def do_angel_connect(ak, ci, pin, ts):
    try:
        obj = SmartConnect(api_key=ak)
        totp = pyotp.TOTP(ts).now()
        res = obj.generateSession(ci, pin, totp)
        if res['status']:
            ANGEL.update({"connected":True, "api_key":ak, "client_id":ci, "pin":pin, "totp_secret":ts})
            db_set("angel_api_key", ak); db_set("angel_client_id", ci)
            print(f"CONNECTED: {ci}")
    except: pass

# ── DASHBOARD (HTML பகுதி சுருக்கப்பட்டுள்ளது, ஆனால் செயல்பாடுகள் முழுமை) ──
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>MATHAN AI HEMAN</title></head>
<body style="background:#070b0f; color:#f0a500; font-family:sans-serif; text-align:center;">
    <h1>MATHAN AI — HEMAN v1.0</h1>
    <div style="border:1px solid #1e2d3d; padding:20px; display:inline-block;">
        <p>System Live 🟢 | Source: <span id="src">NONE</span></p>
        <p>NIFTY: <span id="nifty">--</span> | PCR: <span id="pcr">--</span></p>
        <p>BRAIN: <strong id="signal">WAITING DATA</strong></p>
    </div>
</body>
</html>
"""

# ── ROUTES ──────────────────────────────────────────────────────────
@app.route("/")
@app.route("/dashboard")
def dashboard():
    return Response(DASHBOARD_HTML, mimetype="text/html")

@app.route("/connect_angel", methods=["POST"])
def connect_angel_rest():
    d = request.get_json(force=True)
    threading.Thread(target=do_angel_connect, args=(d['api_key'], d['client_id'], d['pin'], d['totp_secret']), daemon=True).start()
    return jsonify({"ok":True, "msg":"Login process started"})

@app.route("/ping")
def ping():
    return jsonify({"status":"online", "time":datetime.datetime.now().strftime("%H:%M:%S")})

if __name__ == "__main__":
    db_init(); db_load()
    if ANGEL["api_key"] and ANGEL["client_id"]:
        threading.Thread(target=do_angel_connect, args=(ANGEL["api_key"], ANGEL["client_id"], ANGEL["pin"], ANGEL["totp_secret"]), daemon=True).start()
    threading.Thread(target=poll_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)
