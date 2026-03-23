import os, json, time, threading, datetime, socket, requests, sqlite3
import pyotp
try:
    from SmartApi import SmartConnect
    SMARTAPI_OK = True
except ImportError:
    SMARTAPI_OK = False
from flask import Flask, Response, jsonify, request

# ── DASHBOARD HTML ────────────────────────────────────────────────────
# (மதன் சார், உங்கள் கோப்பில் இருந்த அதே முழுமையான HTML பகுதி இங்கே இருக்கும்)

app  = Flask(__name__)

# ── CONFIG ─────────────────────────────────────────────────────────
PORT         = int(os.environ.get("PORT", 8000))
DB           = "/tmp/mathan_brain.db"
SCRIP_URL    = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
SCRIP_CACHE  = "/tmp/angel_scrip_master.json"

INDEX_CFG = {
    "NIFTY":  {"step": 50,  "lot": 75,  "token": "26000", "exchange": "NSE"},
    "SENSEX": {"step": 100, "lot": 20,  "token": "1",     "exchange": "BSE"},
}

# (மற்ற அனைத்து மார்க்கெட் லாஜிக் மற்றும் ஏஜென்ட் விபரங்கள் இங்கே தொடரும்...)

# ── ROUTES ──────────────────────────────────────────────────────────

@app.route("/connect_angel", methods=["POST"])
def connect_angel_rest():
    data       = request.get_json(force=True) or {}
    api_key     = data.get("api_key","").strip()
    client_id   = data.get("client_id","").strip()
    pin         = data.get("pin","").strip()
    totp_secret = data.get("totp_secret","").strip()
    if not all([api_key, client_id, pin, totp_secret]):
        return jsonify({"ok":False,"error":"All 4 fields required"}), 400
    threading.Thread(
        target=do_angel_connect,
        args=(api_key, client_id, pin, totp_secret),
        daemon=True
    ).start()
    return jsonify({"ok":True,"msg":"Login started"})

@app.route("/ping")
def ping():
    return jsonify({"pong": True, "time": datetime.datetime.now().strftime("%H:%M:%S")})

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return Response(DASHBOARD_HTML, mimetype="text/html")

if __name__ == "__main__":
    db_init()
    db_load()

    # Auto-login if credentials saved
    if ANGEL["api_key"] and ANGEL["client_id"] and ANGEL["pin"] and ANGEL["totp_secret"]:
        threading.Thread(
            target=do_angel_connect,
            args=(ANGEL["api_key"], ANGEL["client_id"], ANGEL["pin"], ANGEL["totp_secret"]),
            daemon=True
        ).start()

    threading.Thread(target=poll_loop, daemon=True).start()
    
    print(f"Starting HEMAN on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)
