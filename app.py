import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "<h1>MATHAN AI HEMAN LIVE!</h1>"

@app.route("/ping")
def ping():
    return jsonify({"status": "OK", "system": "HEMAN"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
