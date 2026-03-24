from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "MATHAN AI HEMAN - LIVE!"

@app.route("/ping")
def ping():
    return jsonify(status="OK")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)