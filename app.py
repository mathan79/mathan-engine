import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>MATHAN AI HEMAN LIVE!</h1>"

@app.route("/ping")
def ping():
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)